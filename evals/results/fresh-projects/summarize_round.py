import hashlib
import itertools
import json
import statistics
import sys
from pathlib import Path

r = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else Path(__file__).resolve().parent / 'final'
rows=[];missing=[]
tasks = [json.loads(line) for line in (r / 'tasks.jsonl').read_text().splitlines()] if (r / 'tasks.jsonl').exists() else []
expected = {(x['case_id'], x['variant'], x['run_number']) for x in tasks}
if not expected:
 expected = {(c['id'], arm, run) for c in json.loads((r / 'manifest.json').read_text())['cases'] for arm in ['old_skill','with_skill'] for run in [1,2,3]}
for case in sorted({x[0] for x in expected}):
 for arm in ['old_skill','with_skill']:
  for run in sorted(x[2] for x in expected if x[:2] == (case, arm)):
   base=r/'runs'/case/arm/('run-'+str(run))
   jid=f'{case}::{arm}::run-{run}::audit-quality';opaque='candidate-'+hashlib.sha256(('blind-v1:'+jid).encode()).hexdigest()[:18]
   judge=r/'judges-codex'/(opaque+'.json')
   if not (base/'metadata.json').exists() or not judge.exists():missing.append([case,arm,run]);continue
   meta=json.loads((base/'metadata.json').read_text());j=json.loads(judge.read_text())
   if meta.get('returncode')!=0 or j.get('parse_error') or j.get('returncode')!=0:raise ValueError('Invalid run/judgment '+str(base))
   usage={}
   for line in (base/'trace.jsonl').read_text().splitlines():
    e=json.loads(line)
    if e.get('type')=='turn.completed':usage=e.get('usage',{})
   dims=j['dimension_scores'];quality=statistics.mean((v-1)/4 for v in dims.values())
   events=json.loads((base/'events.json').read_text())['events']
   commands=[e.get('input_summary','') for e in events if e.get('type')=='command' and e.get('status')=='completed']
   row={'case':case,'variant':arm,'run':run,'source_round':('round-3-bytego' if case=='fresh-bytego' else 'round-2') if r.name=='final' else r.name,'dimensions':dims,'quality':quality,'quality_threshold_pass':quality>=0.85,'judge_rationale':j.get('evidence'),'output_sha256':hashlib.sha256((base/'output.md').read_bytes()).hexdigest(),'model':meta.get('model'),'elapsed_seconds':meta['elapsed_ms']/1000,'usage':usage,'completed_shell_commands':len(commands),'skill_read_observed':any('SKILL.md' in c and 'skills/' in c for c in commands),'scanner_observed':any('cfdoctor_static_scan.py' in c for c in commands),'out_of_workspace_handles':any('/Users/' in c or 'matched-eval' in c or 'hidden-scoring' in c for c in commands)}
   rows.append(row)
if missing and '--allow-incomplete' not in sys.argv:raise ValueError('Incomplete final set '+str(missing))
byarm={}
for arm in ['old_skill','with_skill']:
 subset=[x for x in rows if x['variant']==arm]
 if not subset:continue
 byarm[arm]={'n':len(subset),'dimension_means':{k:statistics.mean(x['dimensions'][k] for x in subset) for k in ['recall','precision','actionability','evidence']},'quality_mean':statistics.mean(x['quality'] for x in subset),'quality_passes':sum(x['quality_threshold_pass'] for x in subset),'mean_total_tokens':statistics.mean(x['usage'].get('input_tokens',0)+x['usage'].get('output_tokens',0) for x in subset),'median_total_tokens':statistics.median(x['usage'].get('input_tokens',0)+x['usage'].get('output_tokens',0) for x in subset),'median_seconds':statistics.median(x['elapsed_seconds'] for x in subset),'mean_seconds':statistics.mean(x['elapsed_seconds'] for x in subset)}
lookup={(x['case'],x['variant'],x['run']):x for x in rows};pairs=[]
for case in sorted({x['case'] for x in rows}):
 for run in [1,2,3]:
  a=lookup.get((case,'with_skill',run));b=lookup.get((case,'old_skill',run))
  if a and b:pairs.append({'case':case,'run':run,'quality_delta':a['quality']-b['quality'],'dimension_deltas':{k:a['dimensions'][k]-b['dimensions'][k] for k in a['dimensions']}})
case_deltas={c:statistics.mean(p['quality_delta'] for p in pairs if p['case']==c) for c in sorted({p['case'] for p in pairs})}
uncertainty={}
if case_deltas:
 d=list(case_deltas.values());observed=statistics.mean(d)
 boot=sorted(statistics.mean(values) for values in itertools.product(d,repeat=len(d)))
 ci=[boot[int(.025*(len(boot)-1))],boot[int(.975*(len(boot)-1))]]
 flips=[statistics.mean(v*s for v,s in zip(d,signs)) for signs in itertools.product([-1,1],repeat=len(d))]
 uncertainty={'case_clusters':len(d),'quality_delta':observed,'bootstrap_95_ci':ci,'exact_two_sided_sign_flip_p':sum(abs(x)>=abs(observed)-1e-12 for x in flips)/len(flips),'case_deltas':case_deltas}
result={'by_arm':byarm,'paired_runs':len(pairs),'pair_wins':sum(p['quality_delta']>1e-10 for p in pairs),'pair_losses':sum(p['quality_delta']< -1e-10 for p in pairs),'pair_ties':sum(abs(p['quality_delta'])<=1e-10 for p in pairs),'uncertainty':uncertainty,'missing':missing,'pairs':pairs,'runs':rows}
path=r/('summary-interim.json' if missing else 'summary.json');path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['by_arm','paired_runs','pair_wins','pair_losses','pair_ties','uncertainty','missing']},indent=2))
