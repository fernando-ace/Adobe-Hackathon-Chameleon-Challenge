"""Independent content/semantic red team; writes explicit failures, never hides them."""
from copy import deepcopy
import json
from pathlib import Path
from tools.stress_corpus import make_design
from tools.hardening_benchmark import evaluate


def main():
    cases=[]
    for length in (120,400):
     s,_=make_design(20261020,5);next(e for e in s['elements'] if e['id']=='headline')['content']='W'*length
     cases.append((f'UNBREAKABLE_{length}','RED_TEAM',s,dict(width=320,height=50)))
    s,_=make_design(20261021,8);next(e for e in s['elements'] if e['id']=='headline')['content']='A fixed line\n'*11+'Final fixed line'
    cases.append(('EXPLICIT_NEWLINES','RED_TEAM',s,dict(width=728,height=90)))
    s,_=make_design(20261022,8);hero=next(e for e in s['elements'] if e['id']=='hero')
    for i in range(27):
     e=deepcopy(hero);e.update(id=f'new_hero_{i}',x=20+(i%6)*150,y=330+(i//6)*130,width=100,height=100);s['elements'].append(e)
    cases.append(('MANY_HEROES_35','RED_TEAM',s,dict(width=728,height=90)))
    s,_=make_design(20261023,8);cta=[e for e in s['elements'] if e.get('group_id')=='cta']
    for i in range(4):
     for old in cta:
      e=deepcopy(old);e.update(id=old['id']+str(i),group_id='extra_action'+str(i));e['y']-=100*(i+1);s['elements'].append(e)
    cases.append(('MULTIPLE_ACTIONS','RED_TEAM',s,dict(width=480,height=1920)))
    s,_=make_design(20261024,8);next(e for e in s['elements'] if e['id']=='headline')['content']='Été — München • Łódź, ação e celebração'
    cases.append(('UNICODE_COPY','RED_TEAM',s,dict(width=320,height=50)))
    s,_=make_design(20261025,15)
    for e in s['elements']:
     if e['id']!='bg':e['y']*=.12
    cases.append(('SOURCE_WHITESPACE','RED_TEAM',s,dict(width=1080,height=1920)))
    s,_=make_design(20261026,30);sw,sh=s['canvas'].values()
    for e in s['elements']:
     e['x']*=2400/sw;e['width']*=2400/sw;e['y']*=400/sh;e['height']*=400/sh
    s['canvas']=dict(width=2400,height=400)
    cases.append(('DENSE_WIDE_TO_TALL','RED_TEAM',s,dict(width=180,height=1600)))
    Path('work').mkdir(exist_ok=True)
    rows=[evaluate((c,True)) for c in cases]
    Path('work/redteam.json').write_text(json.dumps(dict(cases=rows),indent=2)+'\n')
    print([(r['case'],r['collisions'],r['clipping'],r['fallback'],r['headline']) for r in rows])


if __name__ == "__main__":
    main()
