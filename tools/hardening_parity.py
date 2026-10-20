"""Compare serial outputs with independent process-worker benchmark outputs."""
import argparse
from pathlib import Path
import json
from tools.hardening_benchmark import cases, evaluate


def main():
    p=argparse.ArgumentParser();p.add_argument('--references',nargs='+',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--per-split',type=int,default=100)
    a=p.parse_args();results=[]
    for path in a.references:
        data=json.loads(path.read_text());split=data['split']
        if split=='legacy':continue
        rows=data['cases'];lookup={c[0]:c for c in cases(split,len(rows))}
        selected=rows[::max(1,len(rows)//a.per_split)][:a.per_split]
        mismatches=[]
        for row in selected:
            serial=evaluate((lookup[row['case']],False))
            if serial['digest']!=row['digest']:mismatches.append(row['case'])
        results.append(dict(split=split,checked=len(selected),mismatches=mismatches))
    result=dict(label='Independent design workers, not internal parallel candidate search',splits=results,
                checked=sum(r['checked'] for r in results),failures=sum(len(r['mismatches']) for r in results))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
