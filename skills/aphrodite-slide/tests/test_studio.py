"""Comprehensive automated test suite for Aphrodite-slide v2."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from studio import paths
from studio.html import build as build_html
from studio.outline import approve, diff, guard, lint, parse, scaffold_outline, to_spec
from studio.recommend import recommend
from studio.registry import apply_template, get_template, list_templates, sample_deck
from studio.spec import audit, list_themes, load_deck, normalize, safe_local_image
from studio.templates import create_theme, privacy_scan, save_template, test_template

HAS_PPTX = importlib.util.find_spec('pptx') is not None
HAS_PLAYWRIGHT = importlib.util.find_spec('playwright') is not None


class AphroditeStudioV2Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='aph_test_')
        self.tmp = Path(self._tmp.name)
        self._env = mock.patch.dict(os.environ, {'APHRODITE_HOME': str(self.tmp / 'home')})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    # ------------------------------------------------------------------ 1. Package & Spec Compliance
    def test_doctor_and_single_skill_rule(self):
        proc = subprocess.run([sys.executable, str(SKILL_DIR / 'scripts/doctor.py')],
                              cwd=str(self.tmp), capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn('PASS: aphrodite-slide', proc.stdout)
        skill_mds = list(SKILL_DIR.rglob('SKILL.md'))
        self.assertEqual(len(skill_mds), 1)
        self.assertEqual(skill_mds[0].resolve(), (SKILL_DIR / 'SKILL.md').resolve())

    def test_cli_works_from_external_cwd(self):
        cli = str(SKILL_DIR / 'scripts/studio.py')
        proc = subprocess.run(
            [sys.executable, cli, 'recommend', '--brief', 'Bảo vệ khóa luận tốt nghiệp đại học'],
            cwd=str(self.tmp), capture_output=True, text=True, encoding='utf-8', check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data['recommended'], 'academic-defense')

    # ------------------------------------------------------------------ 2. Schema, v1 Compat, Glyphs & Security
    def test_v1_logistics_backward_compatibility(self):
        d = load_deck(SKILL_DIR / 'examples/logistics/deck.json')
        norm = normalize(d)
        self.assertEqual(norm['theme'], 'editorial-warm')  # aliased from v1 editorial-cream
        rep = audit(d, strict=True)
        self.assertTrue(rep['ok'], rep['issues'])
        self.assertEqual(rep['slide_count'], 9)

    def test_evidence_and_duplicate_id_gates(self):
        d = {
            'title': 'Test',
            'slides': [{'id': 's1', 'layout': 'metrics', 'title': 'Tăng 45% sản lượng', 'items': [{'value': '45%', 'label': 'sản lượng'}]}],
        }
        rep = audit(d, strict=True)
        self.assertFalse(rep['ok'])
        self.assertTrue(any(x['code'] == 'unsourced-number' for x in rep['issues']))
        d['slides'][0]['data_status'] = 'illustrative'
        self.assertTrue(audit(d, strict=True)['ok'])

        dup = {'title': 'Dup', 'slides': [{'id': 'a', 'layout': 'cover', 'title': 'A'}, {'id': 'a', 'layout': 'closing', 'title': 'B'}]}
        self.assertFalse(audit(dup, strict=True)['ok'])

    def test_filler_and_capacity_warnings(self):
        d = {
            'title': 'Test',
            'demo': True,
            'slides': [{
                'id': 's1', 'layout': 'statement',
                'title': 'Hãy cùng khám phá giải pháp toàn diện vượt trội trong kỷ nguyên mới',
            }],
        }
        rep = audit(d, strict=False)
        codes = {x['code'] for x in rep['issues']}
        self.assertIn('filler', codes)

    def test_local_image_sanitization(self):
        self.assertEqual(safe_local_image('charts/overview.png'), 'charts/overview.png')
        for bad in ('../secret.png', 'https://example.com/a.png', '/etc/passwd', 'javascript:alert(1)', 'a.png?x=1', 'a\\b.png'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    safe_local_image(bad)

    def test_vietnamese_glyph_coverage_across_all_themes(self):
        vi_sample = 'Điều phối thông minh: kết quả học tập, ngưỡng cảnh báo, tỷ lệ đỗ 98,5% ở bậc đại học.'
        for th in list_themes():
            d = {'title': 'Kiểm tra tiếng Việt', 'theme': th['id'], 'demo': True,
                 'slides': [{'id': 's1', 'layout': 'statement', 'title': vi_sample}]}
            rep = audit(d, strict=True)
            letter_errors = [x for x in rep['issues'] if x['code'] == 'missing-glyph']
            self.assertEqual(letter_errors, [], f"Theme {th['id']} failed Vietnamese glyph check: {letter_errors}")

        cjk = {'title': 'CJK test', 'theme': 'editorial-warm', 'demo': True,
               'slides': [{'id': 's1', 'layout': 'statement', 'title': '漢字テスト'}]}
        rep_cjk = audit(cjk, strict=True)
        self.assertFalse(rep_cjk['ok'])
        self.assertTrue(any(x['code'] == 'missing-glyph' for x in rep_cjk['issues']))

    # ------------------------------------------------------------------ 3. Registry & Deterministic Recommendation
    def test_registry_and_previews_exist(self):
        reg = paths.read_json(paths.ASSETS / 'registry.json')
        ids = {t['id'] for t in reg['templates']}
        self.assertEqual(ids, {'academic-defense', 'lecture-teaching', 'medical-briefing', 'tech-product', 'business-review'})
        for t in list_templates():
            self.assertTrue(Path(t['preview_path']).is_file(), f"Missing preview for {t['id']}")
            self.assertGreaterEqual(len(t.get('storyline', [])), 6)

    def test_recommendation_accuracy_vi_and_en(self):
        cases = [
            ('Bảo vệ khóa luận tốt nghiệp nghiên cứu định lượng trước hội đồng', 'academic-defense'),
            ('PhD thesis defense on urban temperature spatial regression', 'academic-defense'),
            ('Soạn bài giảng Vật lý lớp 11 cho học sinh THPT trên lớp', 'lecture-teaching'),
            ('Interactive classroom lecture for undergraduate biology students', 'lecture-teaching'),
            ('Sinh hoạt chuyên môn bệnh viện về chẩn đoán và điều trị tăng huyết áp', 'medical-briefing'),
            ('Clinical health briefing for nurses on diabetes prevention guidelines', 'medical-briefing'),
            ('Ra mắt sản phẩm phần mềm AI chạy cục bộ và demo cho kỹ sư', 'tech-product'),
            ('SaaS developer platform product launch and live API demo', 'tech-product'),
            ('Báo cáo kết quả kinh doanh quý 3, KPI doanh thu và ngân sách trình Ban giám đốc', 'business-review'),
            ('Quarterly executive business review with revenue KPIs and board decisions', 'business-review'),
        ]
        for brief, expected in cases:
            with self.subTest(brief=brief):
                res = recommend(brief=brief)
                self.assertEqual(res['recommended'], expected, f"Expected {expected} for {brief!r}, got {res['recommended']}")
                self.assertGreaterEqual(len(res['options']), 3)
                self.assertEqual(res['custom_option']['id'], 'custom')
                self.assertIn('phong cách mới', res['custom_option']['label_vi'])

    # ------------------------------------------------------------------ 4. Content-First Outline Workflow
    def test_outline_scaffold_lint_approve_diff_and_guard(self):
        tmpl = get_template('academic-defense')
        ol_path = self.tmp / 'outline.md'
        txt = scaffold_outline(tmpl, meta={
            'title': 'Ảnh hưởng giấc ngủ đến GPA',
            'audience': 'Hội đồng khóa luận',
            'purpose': 'Bảo vệ khóa luận 12 phút',
            'takeaway': 'Ngủ đủ 7–8 giờ gắn với GPA cao hơn.',
        })
        # Replace placeholders with valid concrete content
        ol_clean = (
            "---\n"
            "title: Ảnh hưởng giấc ngủ đến GPA\n"
            "audience: Hội đồng khóa luận\n"
            "purpose: Bảo vệ khóa luận 12 phút\n"
            "takeaway: Ngủ đủ 7–8 giờ gắn với GPA cao hơn.\n"
            "template: academic-defense\n"
            "theme: editorial-warm\n"
            "language: vi\n"
            "density: speaker\n"
            "duration_minutes: 5\n"
            "---\n\n"
            "## 01 · Giấc ngủ và **kết quả học tập** sinh viên\n"
            "- layout: cover\n"
            "- message: Nghiên cứu cắt ngang trên 412 sinh viên năm nhất.\n"
            "- status: illustrative\n\n"
            "## 02 · Nhóm ngủ 7–8 giờ đạt điểm GPA cao nhất (3,21)\n"
            "- layout: chart\n"
            "- message: GPA trung bình tăng rõ ở nhóm ngủ đủ 7–8 giờ.\n"
            "- data: <6h: 2,71 | 7-8h: 3,21\n"
            "- status: illustrative\n"
        )
        self.assertIn('template: academic-defense', txt)
        ol_path.write_text(ol_clean, encoding='utf-8')

        parsed = parse(ol_clean)
        rep = lint(parsed)
        self.assertTrue(rep['ok'], rep['issues'])

        app1 = approve(ol_path, note='v1')
        self.assertTrue(Path(app1['baseline']).is_file())
        d0 = diff(ol_path)
        self.assertEqual(d0['changed'], [])
        self.assertFalse(d0['major_change'])

        # Edit slide 02 data/message and check diff + re-approval history archive
        ol_edited = ol_clean.replace('3,21', '3,28')
        ol_path.write_text(ol_edited, encoding='utf-8')
        d1 = diff(ol_path)
        self.assertEqual(len(d1['changed']), 1)
        self.assertEqual(d1['changed'][0]['num'], '02')
        self.assertTrue(d1['major_change'])

        approve(ol_path, note='v2')
        archives = list((self.tmp / '.aphrodite').glob('outline.baseline.*.json'))
        self.assertGreaterEqual(len(archives), 1)

        spec = to_spec(parse(ol_edited))
        spec['slides'][1]['chart'] = {'type': 'column', 'categories': ['<6h', '7-8h'], 'series': [{'name': 'GPA', 'values': [2.71, 3.28]}]}
        self.assertEqual(guard(spec, ol_path), [])

        # Silent title rewrite triggers off-baseline warning
        spec['slides'][1]['title'] = 'Một tiêu đề khác hoàn toàn không có trong baseline'
        drift = guard(spec, ol_path)
        self.assertTrue(any(x['code'] == 'off-baseline' for x in drift))

    # ------------------------------------------------------------------ 5. HTML Engine, All Templates x Themes, Escaping & Motion
    def test_build_all_templates_across_compatible_themes(self):
        built = 0
        for t in list_templates():
            deck = apply_template(sample_deck(t), t)
            assets = Path(t['_dir']) / 'assets'
            for th in t.get('compatible_themes', [t['default_theme']]):
                dest = self.tmp / f"{t['id']}-{th}"
                res = build_html(deck, dest, theme_name=th, assets_root=assets if assets.is_dir() else None)
                self.assertTrue(res['audit']['ok'])
                html = (dest / 'index.html').read_text(encoding='utf-8')
                self.assertIn('prefers-reduced-motion', html)
                self.assertIn('ArrowRight', html)
                built += 1
        self.assertGreaterEqual(built, 15)

    def test_single_file_html_and_xss_escaping(self):
        d = load_deck(SKILL_DIR / 'examples/gallery/deck.json')
        d['slides'][0]['title'] = 'An toàn <script>alert("xss")</script>'
        dest = self.tmp / 'single'
        build_html(d, dest, assets_root=SKILL_DIR / 'examples/gallery/assets', single_file=True, animation='cinematic')
        html = (dest / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert("xss")</script>', html)
        self.assertIn('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;', html)
        self.assertIn('data:font/woff2;base64,', html)
        self.assertIn('data:image/jpeg;base64,', html)

    # ------------------------------------------------------------------ 6. Custom Design, Privacy Scrub, Versioning & Reuse
    def test_custom_theme_gates_and_template_lifecycle(self):
        # Reject low-contrast theme
        with self.assertRaises(ValueError):
            create_theme('bad-contrast', base='editorial-warm', sets={'colors.ink': '#F5F5F5'}, scope='user')
        # Reject unbundled font
        with self.assertRaises(ValueError):
            create_theme('bad-font', base='editorial-warm', sets={'fonts.display': 'Papyrus'}, scope='user')

        # Valid custom theme
        tp = create_theme('ocean-editorial', base='editorial-warm',
                          sets={'colors.accent': '#0369A1', 'colors.accent_strong': '#075985', 'colors.accent_soft': '#E0F2FE'},
                          scope='user', name='Ocean Editorial')
        self.assertTrue(tp.is_file())

        # Deck containing PII
        src_deck = {
            'title': 'Báo cáo nội bộ M&A',
            'theme': 'ocean-editorial',
            'demo': True,
            'slides': [
                {'id': 's1', 'layout': 'cover', 'title': 'Dự án M&A mật', 'subtitle': 'Liên hệ secret@corp.example.com hoặc 0912345678'},
                {'id': 's2', 'layout': 'metrics', 'title': 'Hai chỉ số thương vụ', 'items': [{'value': '50 tỷ', 'label': 'giá trị'}]},
            ],
        }
        self.assertGreaterEqual(len(privacy_scan(src_deck)), 2)

        # Saving with include_content=True without allow_sensitive must fail
        with self.assertRaises(PermissionError):
            save_template(src_deck, tid='ocean-brief', name='Ocean Brief', use_cases=['business'],
                          scope='user', include_content=True, render=False)

        # Default save scrubs private text into neutral sample
        saved1 = save_template(src_deck, tid='ocean-brief', name='Ocean Brief', use_cases=['business'],
                               scope='user', render=False)
        self.assertEqual(saved1['version'], '1.0.0')
        sample_txt = (Path(saved1['dir']) / 'sample.json').read_text(encoding='utf-8')
        self.assertNotIn('secret@corp.example.com', sample_txt)
        self.assertNotIn('0912345678', sample_txt)

        # Overwrite without --bump must fail
        with self.assertRaises(FileExistsError):
            save_template(src_deck, tid='ocean-brief', name='Ocean Brief', use_cases=['business'],
                          scope='user', render=False)

        # Version bump archives v1.0.0 and creates v1.1.0
        saved2 = save_template(src_deck, tid='ocean-brief', name='Ocean Brief', use_cases=['business'],
                               scope='user', bump='minor', render=False)
        self.assertEqual(saved2['version'], '1.1.0')
        self.assertTrue((Path(saved2['dir']) / 'versions/1.0.0/template.json').is_file())

        # Reuse on an unrelated deck
        other = load_deck(SKILL_DIR / 'examples/logistics/deck.json')
        reuse = test_template('ocean-brief', other_deck=other)
        self.assertTrue(reuse['sample']['ok'])
        self.assertTrue(reuse['other_content']['ok'])
        self.assertEqual(reuse['other_content']['theme'], 'ocean-editorial')

    # ------------------------------------------------------------------ 7. Native Editable PPTX v2 & Structural QA
    @unittest.skipUnless(HAS_PPTX, 'python-pptx not installed')
    def test_pptx_v2_gallery_native_objects_notes_and_entrances(self):
        from studio.pptx import export as export_pptx
        from studio.qa.pptx_qa import inspect_pptx

        gal = load_deck(SKILL_DIR / 'examples/gallery/deck.json')
        gal['slides'][0]['notes'] = 'Ghi chú thuyết trình tiếng Việt cho trang bìa.'
        out_pptx = self.tmp / 'gallery.pptx'
        res = export_pptx(gal, out_pptx, assets_root=SKILL_DIR / 'examples/gallery/assets', transitions=True, entrances=True)
        self.assertEqual(res['slides'], 31)
        self.assertEqual(res['native_charts'], 5)
        self.assertEqual(res['native_tables'], 1)
        self.assertGreaterEqual(res['notes_slides'], 1)

        qa = inspect_pptx(out_pptx)
        self.assertTrue(qa['ok'], qa['issues'])
        self.assertEqual(qa['native_charts'], 5)
        self.assertEqual(qa['native_tables'], 1)
        self.assertEqual(qa['transitions'], 31)
        self.assertEqual(qa['entrances'], 31)

    # ------------------------------------------------------------------ 8. Live Browser Render & Motion QA (Optional)
    @unittest.skipUnless(HAS_PLAYWRIGHT, 'playwright not installed')
    def test_playwright_render_pdf_and_motion_qa(self):
        from studio.qa import evaluate
        from studio.render import render

        deck = {
            'title': 'Kiểm thử Render & Animation',
            'audience': 'QA',
            'takeaway': 'Mọi thành phần hiển thị đầy đủ sau hiệu ứng.',
            'theme': 'editorial-warm',
            'animation': 'professional',
            'build': True,
            'demo': True,
            'slides': [
                {'id': 'cover', 'layout': 'cover', 'eyebrow': 'QA', 'title': 'Kiểm thử **trực quan** tiếng Việt'},
                {'id': 'chart', 'layout': 'chart', 'eyebrow': 'Số liệu', 'title': 'Biểu đồ cột hiển thị rõ nhãn',
                 'chart': {'type': 'column', 'categories': ['Nhóm A', 'Nhóm B', 'Nhóm C'],
                           'series': [{'name': 'Điểm', 'values': [72, 85, 91]}], 'unit': '%'},
                 'insights': ['Nhóm C đạt tỷ lệ cao nhất']},
            ],
        }
        out = self.tmp / 'render-deck'
        b = build_html(deck, out)
        ren = render(out, pdf='both', motion=True)
        qa = evaluate(ren, content=b['audit'], folder=out)
        self.assertTrue(qa['ok'], qa)
        self.assertTrue((out / 'deck.pdf').is_file())
        self.assertTrue((out / 'deck-image.pdf').is_file())
        self.assertTrue((out / 'contact-sheet.jpg').is_file())
        self.assertTrue(ren['motion']['keyboard_ok'])


if __name__ == '__main__':
    unittest.main()
