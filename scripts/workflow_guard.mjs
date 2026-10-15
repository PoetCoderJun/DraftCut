import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
export const fileHash=file=>createHash('sha256').update(readFileSync(file)).digest('hex');
export function assertWorkflow(plan,composition) {
 try {
  const result=execFileSync('python3',[fileURLToPath(new URL('./spoken_workflow.py',import.meta.url)),'check','--plan',plan,...(composition?['--composition',composition]:[])],{encoding:'utf8'});
  return JSON.parse(result);
 } catch(e) {throw new Error(e.stderr?.toString().trim()||e.message);}
}
