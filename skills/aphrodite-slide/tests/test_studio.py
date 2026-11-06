import json, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studio.model import audit,load_deck
from studio.html import build,safe_local_image

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'examples/logistics/deck.json'

class StudioTests(unittest.TestCase):
    def test_demo_passes_strict_evidence_audit(self):
        d=load_deck(DEMO);r=audit(d,strict=True)
        self.assertTrue(r['ok'],r['issues']);self.assertEqual(r['slide_count'],9)

    def test_numeric_claim_requires_source_unless_demo(self):
        d={'title':'t','slides':[{'id':'a','type':'metrics','title':'123 shipments','items':[{'value':'123','label':'units'}]}]}
        r=audit(d,strict=True)
        self.assertFalse(r['ok']);self.assertIn('numeric claim',str(r['issues']))
        d['slides'][0]['illustrative']=True;d['slides'][0]['note']='demo';self.assertTrue(audit(d,strict=True)['ok'])

    def test_duplicate_slide_ids_rejected(self):
        d={'title':'t','slides':[{'id':'x','type':'cover','title':'a'},{'id':'x','type':'cover','title':'b'}]}
        self.assertFalse(audit(d,strict=True)['ok'])

    def test_local_images_are_sanitized(self):
        self.assertEqual(safe_local_image('illustration/chart.svg'),'illustration/chart.svg')
        for s in ['../../secret.svg','https://example.com/x.png','/tmp/test.png','javascript:test.svg','x.png?version=1','foo\\bar.jpg']:
            with self.subTest(s=s):
                with self.assertRaises(ValueError):safe_local_image(s)

    def test_html_generation_all_themes(self):
        d=load_deck(DEMO)
        with tempfile.TemporaryDirectory() as dirname:
            for theme in ('editorial-cream','keynote-night','swiss-contrast'):
                dest=Path(dirname)/theme; files=build(d,dest,theme)
                self.assertEqual(len(files),9)
                self.assertTrue((dest/'index.html').exists())
                first=(dest/'slides'/files[0]).read_text(encoding='utf-8')
                self.assertIn('DỮ LIỆU MINH HỌA',first)
                self.assertIn('Điều phối xe container',first)
                self.assertIn('ArrowRight',(dest/'index.html').read_text(encoding='utf-8'))

    def test_html_escape_text(self):
        d=load_deck(DEMO);d['slides'][0]['title']='<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as dirname:
            names=build(d,Path(dirname))
            result=(Path(dirname)/'slides'/names[0]).read_text(encoding='utf-8')
            self.assertNotIn('<script>alert(1)</script>',result)
            self.assertIn('&lt;script&gt;',result)

if __name__=='__main__':unittest.main()
