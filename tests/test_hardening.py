"""General regression fixtures for extreme-format allocation and feasibility."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from engine.chameleon.allocation import allocated_layout, units, bounds
from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
from engine.chameleon.validator import validate_output
from engine.resize import resize, get_last_diagnostics
from tools.stress_corpus import make_design


class HardeningTests(unittest.TestCase):
    def test_measured_lanes_preserve_contract_and_avoid_dense_collisions(self):
        for count in (8,20,40):
            source,_=make_design(420104,count)
            for target in ({'width':728,'height':90},{'width':180,'height':1600},{'width':1200,'height':628}):
                dna=analyze_design(source,target)
                output=allocated_layout(dna,1)
                self.assertFalse(validate_output(source,target,output))
                report=score_design(dna,output,'allocated')
                self.assertEqual(report.accidental_collision_count,0,report.issues)
                self.assertEqual(report.image_ratio_failures,0,report.issues)
                self.assertEqual(report.off_canvas_count,0,report.issues)

    def test_rotated_text_cells_fit_complete_visual_bounds(self):
        source,_=make_design(420108,8)
        for e in source['elements']:
            if e['id']!='bg':e['rotation']=25
        dna=analyze_design(source,{'width':480,'height':2400})
        output=allocated_layout(dna,1)
        report=score_design(dna,output,'allocated')
        self.assertTrue(report.hard_valid,report.issues)
        self.assertEqual(report.accidental_collision_count,0,report.issues)

    def test_all_unit_members_move_together_with_rotation(self):
        source,_=make_design(420104,20)
        for e in source['elements']:
            if e.get('group_id'):e['rotation']=20
        dna=analyze_design(source,{'width':1600,'height':400})
        output=allocated_layout(dna,2)
        by_id={e['id']:e for e in output['elements']}
        for ids in units(dna):
            if len(ids)<2:continue
            old=[dna.by_id[i].element for i in ids];new=[by_id[i] for i in ids]
            scale=new[0]['width']/old[0]['width']
            for before,after in zip(old,new):
                self.assertAlmostEqual(after['width']/before['width'],scale)
                self.assertAlmostEqual(after['height']/before['height'],scale)

    def test_hierarchy_compaction_keeps_primary_size_and_removes_inversion(self):
        from engine.chameleon.planner import _protect_hierarchy
        source,_=make_design(420104,8)
        dna=analyze_design(source,{'width':728,'height':90})
        out=allocated_layout(dna,1)
        head=next(e for e in out['elements'] if e['id']=='headline')
        head['font_size']=8.
        before=head['font_size']
        _protect_hierarchy(dna,out)
        self.assertEqual(head['font_size'],before)
        report=score_design(dna,out,'allocated_lanes')
        self.assertFalse(any('type hierarchy regressed' in i for i in report.issues))

    def test_identity_shortcut_reflows_substantial_rotated_overflow(self):
        source,_=make_design(420104,8)
        head=next(e for e in source['elements'] if e['id']=='headline')
        head.update(x=0.,y=0.,rotation=35)
        out=resize(source,source['canvas'])
        self.assertNotEqual(get_last_diagnostics()['layout_family'],'identity')
        dna=analyze_design(source,source['canvas'])
        report=score_design(dna,out,get_last_diagnostics()['layout_family'])
        self.assertTrue(report.hard_valid,report.issues)
        self.assertEqual(report.accidental_collision_count,0)

    def test_validator_rejects_zero_size_and_illegal_style_change(self):
        source,_=make_design(420104,8)
        output=deepcopy(source)
        output['elements'][0]['width']=0
        output['elements'][1]['color']='rgba(0,0,0,1)'
        issues=validate_output(source,source['canvas'],output)
        self.assertTrue(any('geometry' in i for i in issues))
        self.assertTrue(any('non-layout property changed: color' in i for i in issues))

    def test_nearby_resize_retains_source_when_source_is_feasible(self):
        source,_=make_design(73,5)
        target={'width':round(source['canvas']['width']*1.03),'height':source['canvas']['height']}
        output=resize(source,target)
        self.assertFalse(validate_output(source,target,output))
        self.assertEqual(get_last_diagnostics()['layout_family'],'source_fit')


if __name__=='__main__':unittest.main()
