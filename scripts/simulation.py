"""Explicit, isolated usability runs. Never a production human identity."""
from __future__ import annotations
import argparse, hashlib, json, secrets, uuid
from datetime import datetime, timezone
from pathlib import Path
from review_approval import canonical, crypto, digest

RUN_SCHEMA='draftcut.simulation-run.v1'
RECEIPT_SCHEMA='draftcut.simulated-user-approval.v1'

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def context(project,manifest):
    ref=manifest.get('simulation_run')
    if not ref:return None
    path=Path(ref['manifest']).resolve();run=json.loads(path.read_text())
    if file_sha(path)!=ref.get('sha256') or run.get('schema')!=RUN_SCHEMA or run.get('scope')!='usability-test-only' or run.get('owner_approval') is not False:
        raise ValueError('Simulation run authorization changed or has invalid scope')
    root=Path(run['run_root']).resolve();project=Path(project).resolve()
    if path!=root/'run.json' or not project.is_relative_to(root/'projects') or run['run_id']!=ref.get('run_id'):
        raise ValueError('Simulation project/run boundary mismatch')
    if manifest['source_sha256']!=run['source_sha256']:
        raise ValueError('Simulation authorization belongs to a different source')
    public=(root/'controller-public.pem').read_text()
    if hashlib.sha256(public.encode()).hexdigest()!=run['public_key_sha256']:
        raise ValueError('Simulation controller trust changed')
    return run,public

def attach(project,manifest,run_path):
    path=Path(run_path).resolve();run=json.loads(path.read_text())
    manifest['simulation_run']={'manifest':str(path),'sha256':file_sha(path),'run_id':run['run_id']}
    context(project,manifest)
    return manifest

def verify(request,receipt,run,public):
    p=receipt.get('payload',{})
    if p.get('schema')!=RECEIPT_SCHEMA or p.get('scope')!='usability-test-only' or p.get('actor')!='simulated-user' or p.get('owner_approval') is not False:
        raise ValueError('Expected an isolated simulated-user receipt, never owner approval')
    if p.get('request_sha256')!=digest(request) or p.get('run_id')!=run['run_id'] or p.get('decision')!='approved':
        raise ValueError('Simulated-user approval is stale or belongs to another run')
    if any(p.get(k)!=request.get(k) for k in ('stage','project_id','generation')):
        raise ValueError('Simulated-user approval stage/project/revision mismatch')
    if not p.get('reply','').strip() or not crypto('verify',{'public_key':public,'message':canonical(p),'signature':receipt.get('signature','')})['valid']:
        raise ValueError('Invalid simulated-user approval signature')
    return digest(receipt)

def create(source,run_dir):
    source=Path(source).resolve();root=Path(run_dir).resolve()
    root.mkdir(parents=True,exist_ok=True)
    if any(root.iterdir()):raise ValueError('Use a new empty simulation run; preserve prior runs')
    secret=secrets.token_urlsafe(32);keys=crypto('generate',{'passphrase':secret})
    run={'schema':RUN_SCHEMA,'scope':'usability-test-only','owner_approval':False,'run_id':str(uuid.uuid4()),
         'run_root':str(root),'source':str(source),'source_sha256':file_sha(source),
         'public_key_sha256':hashlib.sha256(keys['public_key'].encode()).hexdigest()}
    for name,value in [('controller-public.pem',keys['public_key']),('controller-private.json',json.dumps({'private_key':keys['private_key'],'passphrase':secret}))]:
        f=root/name;f.write_text(value);f.chmod(0o600)
    (root/'projects').mkdir();(root/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
    return root/'run.json'

def approve(request_path,reply):
    path=Path(request_path).resolve();request=json.loads(path.read_text())
    if not request.get('simulation_run'):raise ValueError('Simulation controller cannot sign production requests')
    from spoken_workflow import validate_request
    validate_request(request,path)
    p=Path(request['project_dir']);manifest=json.loads((p/'source.json').read_text());run,public=context(p,manifest)
    if request['simulation_run']!=manifest['simulation_run']:raise ValueError('Request simulation scope mismatch')
    keys=json.loads((Path(run['run_root'])/'controller-private.json').read_text())
    payload={'schema':RECEIPT_SCHEMA,'scope':'usability-test-only','actor':'simulated-user','owner_approval':False,
             'run_id':run['run_id'],'request_sha256':digest(request),'stage':request['stage'],'project_id':request['project_id'],
             'generation':request['generation'],'decision':'approved','reply':reply,'issued_at':datetime.now(timezone.utc).isoformat()}
    signature=crypto('sign',{'private_key':keys['private_key'],'passphrase':keys['passphrase'],'message':canonical(payload)})['signature']
    receipt={'payload':payload,'signature':signature};verify(request,receipt,run,public)
    output=path.parent/'approval.json'
    if output.exists():verify(request,json.loads(output.read_text()),run,public)
    else:output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return output

def main():
    a=argparse.ArgumentParser(description=__doc__);s=a.add_subparsers(dest='command',required=True)
    c=s.add_parser('create');c.add_argument('--source',required=True);c.add_argument('--run-dir',required=True)
    c=s.add_parser('approve');c.add_argument('--request',required=True);c.add_argument('--reply',required=True)
    x=a.parse_args();print(create(x.source,x.run_dir) if x.command=='create' else approve(x.request,x.reply))

if __name__=='__main__':main()
