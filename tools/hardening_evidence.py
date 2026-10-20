"""Render risk-ranked development cases and record source-relative collision forensics."""
import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path
import json
from html import escape

from engine.resize import resize, get_last_diagnostics
from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design, _rotated_bounds, _overlap_ratio
from renderer.converter.convert import render_design_to_png
from tools.hardening_benchmark import cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline-outputs',type=Path)
    a=p.parse_args();data=json.loads(a.results.read_text());rows=data['cases']
    # This tool intentionally refuses blind cases while development tuning is active.
    if data['split']!='development':raise ValueError('Use development evidence for tuning; blind cases remain sealed')
    selected=[]
    risks=[lambda r:r['headline'] or 1e9,lambda r:r['important'] or 1e9,lambda r:r['proxy'],
           lambda r:-r['occupancy'],lambda r:(r['headline'] or 1e9)/max(.05,1-r['occupancy'])]
    if any(r['hierarchy'] for r in rows): risks.append(lambda r:-r['hierarchy'])
    if any(r['collisions'] for r in rows): risks.append(lambda r:-r['collisions'])
    for n in range(20):
        risk=risks[n%len(risks)]
        row=next(r for r in sorted(rows,key=risk) if r['case'] not in selected)
        selected.append(row['case'])
    lookup={c[0]:c for c in cases('development',len(rows))}
    recorded = {r['case']: r['output'] for r in json.loads(a.baseline_outputs.read_text())} if a.baseline_outputs else {}
    a.output.mkdir(parents=True,exist_ok=True)
    cards=[];forensics=[]
    for name in selected:
        _,bucket,source,target=lookup[name];out=resize(source,target);diag=get_last_diagnostics()
        render_design_to_png(out,Path('brand_kit/assets'),a.output/(name+'.png'),Path('brand_kit/fonts'))
        (a.output/(name+'.json')).write_text(json.dumps(out,indent=2)+'\n')
        cards.append(f'<article><h2>{escape(name)} · {bucket} · {target["width"]}×{target["height"]}</h2><img src="{name}.png"><p>{escape(str(diag.get("layout_family")))} · {escape(str(diag.get("issues")))}</p></article>')
    # Diagnose every baseline/new collision, not just the rendered twenty.
    for row in rows:
        if not row['collisions']:continue
        name=row['case'];_,bucket,source,target=lookup[name]
        dna=analyze_design(source,target)
        # Recorded baseline issues identify pairs; source evidence stays available
        # even when the current engine no longer reproduces the original failure.
        for fa,fb in combinations(dna.facts,2):
            prefix=f'{fa.id}/{fb.id}: new overlap'
            issue=next((x for x in row['issues'] if x.startswith(prefix)),None)
            if issue is None:continue
            actual = {str(e['id']): e for e in recorded.get(name,{}).get('elements',[])}
            area = None
            if fa.id in actual and fb.id in actual:
                ax,ay,aw,ah=_rotated_bounds(actual[fa.id]);bx,by,bw,bh=_rotated_bounds(actual[fb.id])
                area=max(0.,min(ax+aw,bx+bw)-max(ax,bx))*max(0.,min(ay+ah,by+bh)-max(ay,by))
            roles=[fa.role,fb.role]
            category=('ROTATION_BOUNDS' if any(abs(float(f.element.get('rotation',0)))>0 for f in (fa,fb)) else
                      'GROUP_GROUP' if fa.group_id and fb.group_id else
                      'TEXT_TEXT' if fa.type==fb.type=='text' else
                      'HEADLINE_HERO' if 'headline' in roles and 'hero_image' in roles else
                      'LOGO_TEXT' if 'logo' in roles else 'INSUFFICIENT_LANE')
            forensics.append(dict(case=name,source_canvas=source['canvas'],target=target,elements=len(source['elements']),
                                  family=row['family'],pair=[fa.id,fb.id],roles=roles,category=category,
                                  source_overlap_ratio=_overlap_ratio(fa.element,fb.element),collision_area_px2=area,issue=issue,
                                  visual_review='not individually reviewed; conservative rotated AABB proxy',
                                  repair_attempts=row.get('repairs',0),root_cause='fixed anchors/overflowing semantic bands or unchecked identity' ))
    (a.output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Development risk gallery</title><style>body{font:14px system-ui;max-width:1200px;margin:auto}article{padding:20px;border-bottom:1px solid #ccc}img{max-width:100%;max-height:800px}p{overflow-wrap:anywhere}</style><h1>20 development risks — internal metrics</h1>'+''.join(cards))
    (a.output/'collision-forensics.json').write_text(json.dumps(dict(categories=dict(Counter(r['category'] for r in forensics)),pairs=forensics),indent=2)+'\n')
    print(json.dumps(dict(rendered=selected,collision_categories=dict(Counter(r['category'] for r in forensics)))))

if __name__=='__main__':main()
