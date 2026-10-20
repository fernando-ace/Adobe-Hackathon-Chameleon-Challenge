"""Content-measured semantic lanes with disjoint rotation-aware unit cells.

All source elements survive. Search varies image allocation, secondary columns,
and priority compression; source wrapping is never assumed appropriate.
"""
from __future__ import annotations
from copy import deepcopy
from math import cos, sin, radians, ceil, sqrt
from typing import Any

from .model import DesignDNA, typography_growth
from .scoring import _rotated_bounds
from .typography import measure_text, fit_font_size


def units(dna: DesignDNA) -> list[list[str]]:
    seen = set(dna.background_ids)
    result = []
    for fact in dna.facts:
        if fact.id in seen: continue
        ids = [i for i in dna.groups.get(fact.group_id, [fact.id]) if i not in seen]
        if ids:
            result.append(ids); seen.update(ids)
    return result


def bounds(elements):
    boxes = []
    for e in elements:
        x,y,w,h = _rotated_bounds(e)
        boxes.append((min(x,e['x']),min(y,e['y']),max(x+w,e['x']+e['width']),max(y+h,e['y']+e['height'])))
    return min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)


def text_options(e, width, size):
    """Evaluate full width plus one/two/three-line widths at the requested size."""
    angle = radians(float(e.get('rotation',0)))
    c,s = abs(cos(angle)),abs(sin(angle))
    natural = measure_text(e,1e8,1e8,size).widest_line
    widths = sorted({max(1.,width*f) for f in (1.,.8,.6,.4,.25,.15,.08)} |
                    {max(1.,min(width,natural/n+.5)) for n in (1,2,3,4,6,8)},reverse=True)
    choices=[]
    for w in widths:
        m=measure_text(e,w,1e8,size)
        h=max(1.,m.required_height+.1)
        rw,rh=c*w+s*h,s*w+c*h
        if m.widest_line<=w+.01 and rw<=width+.01:
            choices.append((rh,w,h,m.line_count))
    return sorted(choices)


def place_unit(dna, output, ids, cell):
    """Fit a complete group into its reserved cell, never clamp children alone."""
    x,y,w,h=cell
    originals=[dna.by_id[i].element for i in ids]
    if len(ids)==1 and originals[0].get('type')=='text':
        e=originals[0]; maximum=float(e.get('font_size',12))*typography_growth(dna)
        if abs(float(e.get('rotation',0))) < 1e-8:
            size,m=fit_font_size(e,w,h,maximum=maximum)
            bh=min(h,max(1.,m.required_height))
            output[ids[0]].update(x=x,y=y+(h-bh)/2,width=w,height=bh,font_size=size)
            return
        lo,hi=1.,max(1.,maximum); best=None
        for _ in range(12):
            size=(lo+hi)/2
            options=[o for o in text_options(e,w,size) if o[0]<=h+.01 and o[2]<=h+.01]
            if options: best=(size,options[0]);lo=size
            else: hi=size
        if best is None:
            options=text_options(e,w,1.)
            best=(1.,options[0] if options else (h,w,h,1))
        size,(_rh,bw,bh,_lines)=best
        output[ids[0]].update(x=x+(w-bw)/2,y=y+(h-bh)/2,width=bw,height=bh,font_size=size)
        return
    x0,y0,x1,y1=bounds(originals)
    scale=min(w/max(1e-6,x1-x0),h/max(1e-6,y1-y0),1.25)
    dx=x+(w-(x1-x0)*scale)/2;dy=y+(h-(y1-y0)*scale)/2
    for eid,e in zip(ids,originals):
        out=output[eid]
        out.update(x=dx+(e['x']-x0)*scale,y=dy+(e['y']-y0)*scale,
                   width=e['width']*scale,height=e['height']*scale)
        if e.get('type')=='text':
            size,_=fit_font_size(e,out['width'],out['height'],maximum=min(float(e.get('font_size',12)),float(e.get('font_size',12))*scale))
            out['font_size']=size


def _role(dna,ids):
    return max((dna.by_id[i] for i in ids),key=lambda f:f.importance).role


def _height(dna,ids,width,factor):
    facts=[dna.by_id[i] for i in ids]
    role=_role(dna,ids)
    if len(ids)==1 and facts[0].type=='text':
        e=facts[0].element
        exponent=.55 if role in {'headline','event_metadata'} else .8 if role=='cta_text' else 1.25 if role=='legal' else 1.
        size=max(1.,float(e.get('font_size',12))*typography_growth(dna)*factor**exponent)
        if abs(float(e.get('rotation',0))) < 1e-8:
            m=measure_text(e,width,1e8,size)
            return max(1.,m.required_height+.1) if m.widest_line<=width+.01 else 1e6
        opts=text_options(e,width,size)
        return opts[0][0] if opts else 1e6
    x0,y0,x1,y1=bounds([f.element for f in facts])
    # Compact secondary groups before sacrificing headline type. Preserve all
    # internal geometry, including rotation and relative alignment.
    scale=min(1.25,width/max(1e-6,x1-x0))*factor**(.9 if role.startswith('cta') else 1.2)
    desired=max(1.,(y1-y0)*scale)
    if all(f.type=='image' for f in facts):
        desired=min(desired,float(dna.target_canvas['height'])*(.075 if role=='logo' else .22))
    elif role=='decoration':
        desired=min(desired,float(dna.target_canvas['height'])*.04)
    return desired


def stack_cells(dna, groups, rect, gap, columns=1):
    """Find a priority-aware compression level, then allocate measured row heights."""
    if not groups: return []
    x,y,w,h=rect
    columns=max(1,min(columns,len(groups)))
    cell_w=(w-gap*(columns-1))/columns
    rows=[groups[i:i+columns] for i in range(0,len(groups),columns)]
    def heights(f):return [max(_height(dna,ids,cell_w,f) for ids in row) for row in rows]
    lo,hi=.001,1.
    for _ in range(13):
        mid=(lo+hi)/2
        if sum(heights(mid))+gap*(len(rows)-1)<=h:lo=mid
        else:hi=mid
    hs=heights(lo)
    available=max(.001,h-gap*(len(rows)-1))
    # At physically impossible sizes still use bounded cells; feasibility
    # validation reports any text that cannot fit at the contractual 1px floor.
    if sum(hs)>available:hs=[hh*available/sum(hs) for hh in hs]
    result=[]
    for row,hh in zip(rows,hs):
        for j,ids in enumerate(row):result.append((ids,(x+j*(cell_w+gap),y,cell_w,hh)))
        y+=hh+gap
    return result


def allocated_layout(dna: DesignDNA, variant: int=0) -> dict[str,Any]:
    output=deepcopy(dna.source);output['canvas']=dict(dna.target_canvas)
    by_id={str(e['id']):e for e in output['elements']}
    cw,ch=float(dna.target_canvas['width']),float(dna.target_canvas['height'])
    for eid in dna.background_ids:by_id[eid].update(x=0.,y=0.,width=cw,height=ch)
    all_units=units(dna)
    # Stable semantic order, with source order as the tie breaker.
    order={'logo':0,'headline':1,'hero_image':2,'supporting_image':2,'subheadline':3,'event_metadata':3,
           'body_copy':4,'cta_text':5,'badge_text':6,'ribbon_text':6,'legal':7,'decoration':8}
    all_units.sort(key=lambda ids:order.get(_role(dna,ids),6))
    images=[ids for ids in all_units if all(dna.by_id[i].type=='image' for i in ids)]
    narrative=[ids for ids in all_units if any(dna.by_id[i].type=='text' and dna.by_id[i].role in {'headline','subheadline','body_copy','event_metadata'} for i in ids)]
    rest=[ids for ids in all_units if ids not in images and ids not in narrative]
    margin=min(cw,ch)*(.025,.04,.06)[variant%3]
    gap=max(.3,min(cw,ch)*.015)
    x,y,w,h=margin,margin,cw-2*margin,ch-2*margin
    cells=[]
    if dna.target_aspect>=1.6:
        # Narrow hero/logo rail; width variants explicitly compete with headline
        # wrapping. Remaining elements occupy measured residual rows below copy.
        rail_share=(.12,.22,.32)[variant%3] if images else 0.
        rail_w=w*rail_share
        copy_w=w-rail_w-(gap if images else 0)
        if images:
            image_h=(h-gap*(len(images)-1))/len(images)
            for i,ids in enumerate(images):cells.append((ids,(x+copy_w+gap,y+i*(image_h+gap),rail_w,image_h)))
        heads=[ids for ids in narrative if _role(dna,ids)=='headline']
        support=[ids for ids in narrative if ids not in heads]
        strategy=(variant//3)%4
        actions=[ids for ids in rest if _role(dna,ids)=='cta_text']
        if strategy==3 and heads and actions:
            # Give rotated action groups a full-height end lane; shrinking a
            # button into the footer often destroys its label before its shape.
            action_w=copy_w*.23
            main_w=copy_w-action_w-gap
            cells+=stack_cells(dna,actions,(x+main_w+gap,y,action_w,h),gap)
            lower=support+[ids for ids in rest if ids not in actions]
            rh=h*min(.65,.20+.025*len(lower)) if lower else 0.
            if lower:
                cols=max(1,min(len(lower),round(sqrt(len(lower)*main_w/max(1.,rh)))))
                cells+=stack_cells(dna,lower,(x,y+h-rh,main_w,rh),gap,cols)
            cells+=stack_cells(dna,heads,(x,y,main_w,h-rh-(gap if lower else 0)),gap)
        elif strategy==2 and heads and (support or rest):
            # An independent supporting column lets the headline use the full
            # banner height. This is a distinct wrap/width tradeoff, not another
            # margin-only candidate.
            secondary_w=copy_w*.30
            main_w=copy_w-secondary_w-gap
            cells+=stack_cells(dna,heads,(x,y,main_w,h),gap)
            cells+=stack_cells(dna,support+rest,(x+main_w+gap,y,secondary_w,h),gap)
        else:
            lower=rest+support if strategy==1 else rest
            upper=heads if strategy==1 else narrative
            if lower:
                share = .22 if strategy==0 else min(.72, .22 + .025*len(lower))
                rh=h*share
                cols=max(1,min(len(lower),round(sqrt(len(lower)*copy_w/max(1.,rh)))))
                cells+=stack_cells(dna,lower,(x,y+h-rh,copy_w,rh),gap,cols)
                nh=h-rh-gap
            else:nh=h
            cells+=stack_cells(dna,upper,(x,y,copy_w,nh),gap)
    else:
        # Full-width measured vertical flow, with explicit hero and secondary
        # rows. No fixed y anchors that can overlap as content counts increase.
        head=[ids for ids in narrative if any(dna.by_id[i].role=='headline' for i in ids)]
        support=[ids for ids in narrative if ids not in head]
        logo=[ids for ids in images if _role(dna,ids)=='logo']
        hero=[ids for ids in images if ids not in logo]
        # Put logos and hero units into distinct rows rather than overlaying
        # multiple images in the same anchor.
        metadata=[ids for ids in support if _role(dna,ids)=='event_metadata']
        support=[ids for ids in support if ids not in metadata]
        flow=logo+head+metadata+hero+support+rest
        if len(flow)>10 and variant%3:
            # Dense square/story designs need secondary columns too. A single
            # long stack wastes width and forces every rotated label to shrink.
            primary=logo+head+metadata+hero
            secondary=support+rest
            ph=h*(.42 if dna.target_aspect>=.72 else .35) if primary else 0.
            cells=stack_cells(dna,primary,(x,y,w,ph),gap)
            secondary_h=h-ph-(gap if primary else 0.)
            columns=(2 if variant%3==1 else
                     max(2,min(6,round(sqrt(len(secondary)*w/max(1.,secondary_h*.8))))))
            cells+=stack_cells(dna,secondary,(x,y+ph+(gap if primary else 0.),w,secondary_h),gap,columns)
        else:
            cells=stack_cells(dna,flow,(x,y,w,h),gap)
    for ids,cell in cells:place_unit(dna,by_id,ids,cell)
    return output


def emergency_grid(dna: DesignDNA) -> dict[str, Any]:
    """Rare disjoint unit grid; final validation still reports impossible text."""
    output=deepcopy(dna.source); output['canvas']=dict(dna.target_canvas)
    by_id={str(e['id']):e for e in output['elements']}
    cw,ch=float(dna.target_canvas['width']),float(dna.target_canvas['height'])
    for eid in dna.background_ids:by_id[eid].update(x=0.,y=0.,width=cw,height=ch)
    foreground=units(dna)
    if not foreground:return output
    columns=max(1,min(len(foreground),round(sqrt(len(foreground)*cw/max(1.,ch)))))
    rows=ceil(len(foreground)/columns)
    gap=min(cw/columns,ch/rows)*.03
    for i,ids in enumerate(foreground):
        row,col=divmod(i,columns)
        place_unit(dna,by_id,ids,(col*cw/columns+gap,row*ch/rows+gap,
                                cw/columns-2*gap,ch/rows-2*gap))
    return output
