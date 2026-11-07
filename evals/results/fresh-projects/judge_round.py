"""Blind the variant, then call the shared harness's native judge backend."""
import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path

r=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'harness'))
import skill_benchmark as sb


def main():
 root=Path(sys.argv[1]).resolve();backend=sys.argv[2] if len(sys.argv)>2 else 'codex'
 model='gpt-5.6-sol' if backend=='codex' else 'claude-sonnet-4-6'
 manifest=json.loads((root/'manifest.json').read_text());cases={c['id']:c for c in manifest['cases']}
 tasks=sb.collect_judge_tasks(root/'manifest.json',root/'runs',split='tune',variants=['with_skill','old_skill'])
 if backend=='claude': tasks=[t for t in tasks if t['run_number']==1]
 tasks.sort(key=lambda t:hashlib.sha256(('blind-v1:'+t['judge_task_id']).encode()).hexdigest())
 dest=root/('judges-'+backend);dest.mkdir(exist_ok=True);mapping={}
 def run(task):
  original=task['judge_task_id'];opaque='candidate-'+hashlib.sha256(('blind-v1:'+original).encode()).hexdigest()[:18];mapping[opaque]=original
  result=dest/(opaque+'.json')
  if result.exists(): return json.loads(result.read_text())
  blind=dict(task,judge_task_id=opaque,variant='candidate',run_number=1,run_base=None)
  case=cases[task['case_id']];bundle=json.loads(Path(case['files'][0]).read_text())
  raw='\n\n'.join('SOURCE FILE: '+p+'\n'+s for p,s in bundle['files'].items())
  # Supply raw source so the judge can verify findings beyond the authored key.
  docs='\n\n'.join(Path(f).read_text() for f in case['files'][1:])
  blind['prompt']='Judge only the supplied evidence; do not call tools, browse, or inspect any filesystem. The candidate label is arbitrary and reveals no experimental arm.\n'+case['prompt']+'\n\nRaw source:\n'+raw+'\n\nOfficial documentation snapshots:\n'+docs
  row=sb.run_one_judge_task(blind,transcripts_dir=dest/'transcripts',judge_model=model,judge_backend=backend,codex_cmd='codex exec --config model_reasoning_effort=high',schema_enforcement='strict')
  row.update(judge_task_id=original,case_id=task['case_id'],variant=task['variant'],run_number=task['run_number'],blinded_candidate_id=opaque)
  result.write_text(json.dumps(row,indent=2)+'\n')
  print(json.dumps({'candidate':opaque,'case':task['case_id'],'parse_error':row.get('parse_error'),'returncode':row.get('returncode'),'dimensions':row.get('dimension_scores')}),flush=True)
  return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p: rows=list(p.map(run,tasks))
 rows.sort(key=lambda x:x['judge_task_id'])
 (root/(backend+'-judge-results.jsonl')).write_text(''.join(json.dumps(x)+'\n' for x in rows))
 (dest/'blinding-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
 print('Stored judgments:',len(rows),flush=True)

if __name__=='__main__':main()
