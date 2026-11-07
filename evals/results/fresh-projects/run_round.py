"""Use the pinned harness's native runner, extending only raw-project mounting."""
import concurrent.futures
import json
import random
import sys
import time
from pathlib import Path, PurePosixPath

r=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'harness'))
import skill_benchmark as sb

original_builder=sb.build_skill_workspace

def mount_project(pt,ws):
 skills,inputs=original_builder(pt,ws)
 bundles=[Path(x) for x in pt.input_files if x.endswith('.project.json')]
 if len(bundles)!=1: raise ValueError('Exactly one raw project bundle required')
 bundle=json.loads(bundles[0].read_text())
 dest=ws/'project'; dest.mkdir()
 for name,content in bundle['files'].items():
  p=PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe source path')
  target=dest.joinpath(*p.parts); target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
 # Make mounting independently inspectable without exposing the original repo.
 (ws/'project-source.json').write_text(json.dumps({k:bundle[k] for k in ['repository','commit']},indent=2))
 return skills,inputs+['project/','project-source.json']

sb.build_skill_workspace=mount_project

def main():
 root=Path(sys.argv[1]).resolve()
 rows=sb.load_jsonl(root/'tasks.jsonl')
 pairs={}
 for row in rows: pairs.setdefault((row['case_id'],row['run_number']),[]).append(row)
 rng=random.Random(20261106)
 jobs=list(pairs.values());rng.shuffle(jobs)
 for pair in jobs: rng.shuffle(pair)
 (root/'execution-order.json').write_text(json.dumps([[x['case_id'],x['run_number'],x['variant']] for pair in jobs for x in pair],indent=2)+'\n')
 def run_pair(pair):
  for row in pair:
   dest=root/'runs'/row['run_dir']
   if (dest/'metadata.json').exists(): raise RuntimeError('Refusing to overwrite run '+str(dest))
   sb.run_agent_tasks([row],root/'runs',sb.AGENT_BACKENDS['codex'],timeout=480,codex_cmd='codex exec --config model_reasoning_effort=high')
   meta=json.loads((dest/'metadata.json').read_text())
   print(json.dumps({'case':row['case_id'],'variant':row['variant'],'run':row['run_number'],'returncode':meta.get('returncode'),'elapsed_ms':meta.get('elapsed_ms')}),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for f in concurrent.futures.as_completed([pool.submit(run_pair,p) for p in jobs]): f.result()
 (root/'answers-complete.json').write_text(json.dumps({'completed':True,'answers':len(rows),'finished':time.time()},indent=2)+'\n')

if __name__=='__main__': main()
