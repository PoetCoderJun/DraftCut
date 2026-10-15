#!/usr/bin/env python3
"""Human-owned signing authority. Production trust is outside the editable project."""
from __future__ import annotations
import argparse, getpass, hashlib, json, os, pwd, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TRUST_DIR=Path(pwd.getpwuid(os.getuid()).pw_dir)/'.config/draftcut' # OS identity, not a caller-overridable HOME
TRUST_FILE=TRUST_DIR/'reviewer-public.pem'
PRIVATE_FILE=TRUST_DIR/'reviewer-private.encrypted.pem'

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def crypto(mode,payload):
    p=subprocess.run(['node',str(ROOT/'approval_crypto.mjs'),mode],input=json.dumps(payload),text=True,capture_output=True)
    if p.returncode:raise ValueError('Human approval key/signature verification failed')
    return json.loads(p.stdout)
def issue(request,private_key,passphrase):
    if request.get('simulation_run'):raise ValueError('Production owner identity cannot approve a simulation request')
    if request.get('stage') not in ('manuscript','director'):raise ValueError('Unknown review stage')
    payload={'schema':'draftcut.human-approval.v1','request_sha256':digest(request),'stage':request['stage'],
             'project_id':request['project_id'],'generation':request['generation'],'decision':'approved',
             'issued_at':datetime.now(timezone.utc).isoformat()}
    signed=crypto('sign',{'private_key':private_key,'passphrase':passphrase,'message':canonical(payload)})
    return {'payload':payload,'signature':signed['signature'],'public_key_sha256':hashlib.sha256(signed['public_key'].encode()).hexdigest()}
def verify_receipt(request,receipt,public_key):
    p=receipt.get('payload',{})
    if p.get('schema')!='draftcut.human-approval.v1' or p.get('decision')!='approved' or p.get('request_sha256')!=digest(request):
        raise ValueError('Human approval is missing, forged or stale for this review')
    if any(p.get(k)!=request.get(k) for k in ('stage','project_id','generation')):raise ValueError('Approval project/stage/revision mismatch')
    if receipt.get('public_key_sha256')!=hashlib.sha256(public_key.encode()).hexdigest():raise ValueError('Approval is not from the trusted human reviewer')
    if not crypto('verify',{'public_key':public_key,'message':canonical(p),'signature':receipt.get('signature','')})['valid']:
        raise ValueError('Invalid human approval signature')
    return digest(receipt)
def require_terminal():
    if not sys.stdin.isatty() or not sys.stdout.isatty():raise ValueError('Human signing requires your own interactive terminal; Agent automation must not approve')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('setup');a=sub.add_parser('approve');a.add_argument('--request',type=Path,required=True)
    args=p.parse_args();require_terminal()
    if args.command=='setup':
        if TRUST_FILE.exists() or PRIVATE_FILE.exists():raise ValueError('Reviewer identity already exists; no overwrite')
        secret=getpass.getpass('Choose a human-only signing passphrase (never share with the Agent): ')
        if len(secret)<12 or secret!=getpass.getpass('Repeat passphrase: '):raise ValueError('Use matching passphrases of at least 12 characters')
        keys=crypto('generate',{'passphrase':secret});TRUST_DIR.mkdir(mode=0o700,parents=True,exist_ok=True)
        for f,v in [(PRIVATE_FILE,keys['private_key']),(TRUST_FILE,keys['public_key'])]:
            with f.open('x') as stream:stream.write(v)
            f.chmod(0o600)
        print('Human reviewer configured. Keep your passphrase private.');return
    request=json.loads(args.request.read_text())
    from spoken_workflow import validate_request
    validate_request(request,args.request)
    if request.get('example_only'):raise ValueError('Synthetic fixtures use their separate test authority, not your production identity')
    review=args.request.parent/'review.md'
    if not review.is_file():raise ValueError('Review document is missing')
    if hashlib.sha256(review.read_bytes()).hexdigest()!=request['review_sha256']:raise ValueError('Review document changed')
    print(review.read_text());print('\nRequest digest: '+digest(request))
    confirmation=input('After reviewing/listening, type APPROVE '+digest(request)[:12]+': ')
    if confirmation!='APPROVE '+digest(request)[:12]:raise ValueError('No explicit approval; nothing signed')
    secret=getpass.getpass('Your signing passphrase: ')
    receipt=issue(request,PRIVATE_FILE.read_text(),secret)
    verify_receipt(request,receipt,TRUST_FILE.read_text())
    output=args.request.parent/'approval.json'
    if output.exists():
        verify_receipt(request,json.loads(output.read_text()),TRUST_FILE.read_text());print('This exact review is already approved.');return
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(output)
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,EOFError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
