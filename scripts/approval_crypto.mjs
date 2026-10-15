// No network or package dependency. Private keys/passphrases arrive only on stdin.
import {generateKeyPairSync, createPrivateKey, createPublicKey, sign, verify} from 'node:crypto';
let input='';for await(const chunk of process.stdin)input+=chunk;
const q=JSON.parse(input), mode=process.argv[2];
try {
 if(mode==='generate') {
  const keys=generateKeyPairSync('ed25519');
  console.log(JSON.stringify({public_key:keys.publicKey.export({format:'pem',type:'spki'}),private_key:keys.privateKey.export({format:'pem',type:'pkcs8',cipher:'aes-256-cbc',passphrase:q.passphrase})}));
 } else if(mode==='sign') {
  const key=createPrivateKey({key:q.private_key,format:'pem',passphrase:q.passphrase});
  console.log(JSON.stringify({signature:sign(null,Buffer.from(q.message),key).toString('base64'),public_key:createPublicKey(key).export({format:'pem',type:'spki'})}));
 } else if(mode==='verify') {
  console.log(JSON.stringify({valid:verify(null,Buffer.from(q.message),createPublicKey(q.public_key),Buffer.from(q.signature,'base64'))}));
 } else throw new Error('Unknown crypto operation');
} catch {console.error('Approval signature/key operation failed');process.exitCode=1;}
