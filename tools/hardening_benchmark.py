"""Fixed split robustness evaluation. Blind details stay sealed until tuning ends.

Metrics are source-relative engine proxies, never hidden Adobe scores.
Run from repository root; --workers evaluates independent designs in processes.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import statistics
import time

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design, _rotated_bounds, _overlap_ratio
from engine.chameleon.validator import validate_output
from engine.resize import resize, get_last_diagnostics
from tools.stress_corpus import make_design, make_mutations, make_stress_corpus

SEEDS = {"development": 420100, "holdout": 730100, "blind": 960100}
BUCKETS = ["NORMAL", "CROSS_ORIENTATION", "ULTRA_WIDE", "ULTRA_TALL", "DENSE",
           "TEXT_HEAVY", "LONG_COPY", "GROUP_HEAVY", "ROTATION_HEAVY",
           "INTENTIONAL_OVERLAP", "BACKGROUND_HEAVY", "TRANSPARENT_IMAGES", "MISSING_ASSET"]


def cases(split, size):
    for i in range(size):
        seed = SEEDS[split] + i
        rng = random.Random(seed)
        bucket = BUCKETS[i % len(BUCKETS)]
        count = rng.choice([8, 15, 20, 30, 40, 45]) if bucket in {"DENSE", "TEXT_HEAVY", "GROUP_HEAVY"} else rng.choice([3, 5, 8, 10, 15, 20])
        src, target = make_design(seed, count)
        sw, sh = src["canvas"].values()
        if bucket == "NORMAL":
            target = {"width": round(sw * 1.03), "height": sh}
        elif bucket == "CROSS_ORIENTATION":
            target = {"width": sh, "height": sw}
        elif bucket == "ULTRA_WIDE":
            w, h = rng.choice([(728,90), (320,50), (1600,400), (2400,120)])
            target = {"width": w, "height": h}
        elif bucket == "ULTRA_TALL":
            w, h = rng.choice([(180,1600), (480,2400), (1080,3840)])
            target = {"width": w, "height": h}
        elif bucket == "LONG_COPY":
            next(e for e in src["elements"] if e["type"] == "text")["content"] = "A botanical collection for summer evenings and shared celebrations " * rng.choice([2,3,4])
        elif bucket == "TEXT_HEAVY":
            for e in src["elements"]:
                if str(e["id"]).startswith("decoration"):
                    for key in ("shape_type", "fill_color", "opacity"):
                        e.pop(key, None)
                    e.update(type="text", content="Supporting details for the seasonal collection", font_family="Solstice Sans", font_size=16, color="rgba(255,255,255,1)", z_index=3)
        elif bucket == "ROTATION_HEAVY":
            for e in src["elements"]:
                if e["id"] != "bg": e["rotation"] = rng.choice([-25, -10, 12, 35])
        elif bucket == "INTENTIONAL_OVERLAP":
            hero = next((e for e in src["elements"] if e["id"] == "hero"), None)
            if hero:
                hero.update(x=sw*.12, y=sh*.18, z_index=2)
        elif bucket == "BACKGROUND_HEAVY":
            src["elements"][0]["opacity"] = .75
        elif bucket == "TRANSPARENT_IMAGES":
            for e in src["elements"]:
                if e["type"] == "image" and e["id"] != "bg": e["asset_id"] = "solstice_bottle.png"
        elif bucket == "MISSING_ASSET":
            for e in src["elements"]:
                if e["type"] == "image" and e["id"] != "bg": e["asset_id"] = "missing_hardening.png"
        yield (f"{split}_{i:04d}", bucket, src, target)


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def evaluate(args):
    case, repeat = args
    name, bucket, source, target = case
    start = time.perf_counter()
    output = resize(source, target)
    elapsed = time.perf_counter() - start
    diag = get_last_diagnostics()
    dna = analyze_design(source, target)
    report = score_design(dna, output, diag.get("layout_family", ""))
    out = {str(e["id"]): e for e in output["elements"]}
    heads = [out[f.id]["font_size"] for f in dna.facts if f.type == "text" and f.role == "headline"]
    important = [out[f.id]["font_size"] for f in dna.facts if f.type == "text" and f.role in {"headline", "subheadline", "cta_text"}]
    non_bg = [e for e in output["elements"] if e["id"] not in dna.background_ids]
    # Union area by sweep, not bounding-box area (which hides large dead zones).
    rects = [_rotated_bounds(e) for e in non_bg]
    xs = sorted({max(0,min(target["width"],x)) for r in rects for x in (r[0], r[0]+r[2])})
    area = 0
    for left,right in zip(xs,xs[1:]):
        intervals = sorted((max(0,y),min(target["height"],y+h)) for x,y,w,h in rects if x < right and x+w > left)
        end = 0
        for top,bottom in intervals:
            area += (right-left)*max(0,bottom-max(end,top)); end=max(end,bottom)
    row = dict(case=name, bucket=bucket, source_canvas=source["canvas"], target=target, elements=len(out),
               family=diag.get("layout_family"), candidates=diag.get("candidate_count",0), repairs=diag.get("repair_count",0),
               structural_issues=validate_output(source,target,output), hard_valid=report.hard_valid,
               collisions=report.accidental_collision_count, clipping=report.clipped_text_count,
               off_canvas=report.off_canvas_count, image_ratios=report.image_ratio_failures,
               hierarchy=sum("type hierarchy regressed" in x for x in report.issues), fallback=diag.get("fallback_used",False),
               headline=min(heads) if heads else None, important=min(important) if important else None,
               proxy=report.score, runtime=elapsed, occupancy=area/(target["width"]*target["height"]),
               issues=report.issues, digest=hashlib.sha256(canonical(output)).hexdigest())
    if repeat: row["deterministic"] = canonical(output) == canonical(resize(source,target))
    return row


def quantiles(values):
    vals=sorted(v for v in values if v is not None)
    if not vals: return None
    def q(p):
        pos=(len(vals)-1)*p; lo=int(pos); hi=min(lo+1,len(vals)-1)
        return round(vals[lo]+(vals[hi]-vals[lo])*(pos-lo),6)
    return dict(min=round(vals[0],6),p5=q(.05),p10=q(.1),median=q(.5),p90=q(.9),p95=q(.95),max=round(vals[-1],6))


def summarize(rows):
    return dict(count=len(rows),structural_failures=sum(bool(r["structural_issues"]) for r in rows),
                hard_invalid=sum(not r["hard_valid"] for r in rows),
                **{k:sum(r[k] for r in rows) for k in ("collisions","clipping","off_canvas","image_ratios","hierarchy","fallback")},
                collision_cases=sum(r["collisions"]>0 for r in rows),clipping_cases=sum(r["clipping"]>0 for r in rows),
                determinism_failures=sum(not r.get("deterministic",True) for r in rows),
                **{k:quantiles(r[k] for r in rows) for k in ("headline","important","proxy","runtime","occupancy","candidates")},
                families=dict(Counter(r["family"] for r in rows)))


def main():
    p=argparse.ArgumentParser(); p.add_argument("--split",choices=[*SEEDS,"legacy"],required=True)
    p.add_argument("--size",type=int,default=300); p.add_argument("--workers",type=int,default=1)
    p.add_argument("--output",type=Path,required=True); p.add_argument("--repeat",action="store_true")
    p.add_argument("--seal",action="store_true"); a=p.parse_args()
    if a.split=="legacy":
        tasks=[json.loads(x.read_text()) for x in sorted(Path("input").glob("*.json"))]
        corpus=[(t["task_id"],"OFFICIAL",t["source"],t["target_canvas"]) for t in tasks]
        corpus += [(n,"STRESS",s,t) for n,s,t in make_stress_corpus()]
        corpus += [(n,"MUTATION",s,t) for n,s,t in make_mutations(tasks)]
    else: corpus=list(cases(a.split,a.size))
    jobs=[(c,a.repeat) for c in corpus]
    if a.workers==1: rows=list(map(evaluate,jobs))
    else:
        with ProcessPoolExecutor(a.workers) as pool: rows=list(pool.map(evaluate,jobs))
    result=dict(label="Synthetic source-relative internal proxies; not Adobe hidden performance",split=a.split,seed=SEEDS.get(a.split),
                summary=summarize(rows),buckets={b:summarize([r for r in rows if r["bucket"]==b]) for b in sorted({r["bucket"] for r in rows})})
    # Seal per-case blind results to disk; do not print or inspect during tuning.
    result["cases"]=rows
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))

if __name__=="__main__": main()
