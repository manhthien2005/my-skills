"""Local visual QA, screenshots, image-PDF output, contact sheet, and JSON checks."""
from __future__ import annotations
import json, os, re, base64, mimetypes
from pathlib import Path
from .model import audit


def _start_browser(p):
    exe=os.environ.get('CHROMIUM_EXECUTABLE')
    if exe and Path(exe).exists(): return p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
    for x in ('/usr/bin/chromium','/usr/bin/chromium-browser'):
        if Path(x).exists(): return p.chromium.launch(executable_path=x,headless=True,args=['--no-sandbox'])
    return p.chromium.launch(headless=True,args=['--no-sandbox'])


def capture(folder: Path, pdf: bool=True, strict: bool=False) -> dict:
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image, ImageOps, ImageDraw
    except ImportError as ex:
        raise RuntimeError('Install render dependencies: pip install playwright pillow; python -m playwright install chromium') from ex
    folder=Path(folder).resolve();manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    paths=[folder/'slides'/x for x in manifest['slides']]
    (folder/'previews').mkdir(exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=_start_browser(p)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        for path in paths:
            # Render entirely from memory so restricted environments that block file:// and
            # localhost navigation can still screenshot self-contained HTML offline.
            markup=path.read_text(encoding='utf-8')
            def inline_asset(m):
                rel=m.group(1)
                asset=(folder/'assets'/rel).resolve()
                try:
                    asset.relative_to((folder/'assets').resolve())
                    if asset.is_file():
                        mime=mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
                        return 'src="data:'+mime+';base64,'+base64.b64encode(asset.read_bytes()).decode('ascii')+'"'
                except ValueError:
                    pass
                return m.group(0)
            markup=re.sub(r'src="\.\./assets/([^"<>]+)"',inline_asset,markup)
            page.set_content(markup,wait_until='load')
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(80)
            check=page.evaluate('''() => {
              let slide=document.querySelector('.slide');let bounds=slide.getBoundingClientRect();
              let footer=document.querySelector('.foot');let ft=footer?.getBoundingClientRect().top ?? 9999;
              let clipping=[],footClash=[];for(let el of document.querySelectorAll('.slide *')) {
                if(el.closest('svg, .foot'))continue;
                let r=el.getBoundingClientRect(); if(r.width<1||r.height<1)continue;
                if(r.right>1922||r.left< -2||r.bottom>1082||r.top< -2) clipping.push({tag:el.tagName,cls:el.className?.toString().slice(0,80)});
                if(el.children.length===0&&el.textContent?.trim()&&r.bottom>ft-5)footClash.push({tag:el.tagName,text:el.textContent.trim().slice(0,60)});
              }return {clip:clipping.slice(0,10),footer_clash:footClash.slice(0,10)};
            }''')
            shot=folder/'previews'/(path.stem+'.jpg')
            page.screenshot(path=str(shot),type='jpeg',quality=88,full_page=False)
            results.append({'slide':path.name,'image':str(shot.relative_to(folder)),'clip_count':len(check['clip']),'footer_clash_count':len(check['footer_clash']),'clip':check['clip'],'footer_clash':check['footer_clash']})
        browser.close()
    # Contact sheet: 2 columns, size suitable for visual triage.
    w=800; thumbw=380; thumbh=int(thumbw*9/16); rows=(len(paths)+1)//2
    sheet=Image.new('RGB',(w,rows*(thumbh+48)+22),'#E5E7EB');d=ImageDraw.Draw(sheet)
    for i,path in enumerate(paths):
        im=Image.open(folder/'previews'/(path.stem+'.jpg')).convert('RGB').resize((thumbw,thumbh))
        x=13+(i%2)*400;y=10+(i//2)*(thumbh+48)
        sheet.paste(im,(x,y));d.text((x,y+thumbh+7),path.stem,fill='#1B1B1B')
    sheet.save(folder/'contact-sheet.jpg',quality=90)
    if pdf:
        images=[Image.open(folder/'previews'/(path.stem+'.jpg')).convert('RGB') for path in paths]
        images[0].save(folder/'deck.pdf',format='PDF',save_all=True,append_images=images[1:],resolution=144)
    content=audit(json.loads((folder/'deck.json').read_text(encoding='utf-8')),strict=True)
    fail=sum(x['clip_count'] or x['footer_clash_count'] for x in results)
    report={'ok':not fail and content['ok'],'slide_count':len(results),'visual_error_count':sum(int(bool(x['clip_count'] or x['footer_clash_count'])) for x in results),'content':content,'slides':results,'note':'Visual QA detects overflow/footer collisions; human review of contact-sheet is still required.'}
    (folder/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Rendered {len(results)} slides. Visual errors: {report['visual_error_count']}; content errors: {content['error_count']}. Contact sheet: {folder/'contact-sheet.jpg'}")
    if strict and not report['ok']: raise RuntimeError('QA errors detected; inspect qa-report.json')
    return report
