#!/usr/bin/env python3
"""把 图片/ 素材规范化到 images-ready/，并生成 images-manifest.json（文件名/Title/Alt/用途）。
原图只读，不做任何修改。重复运行幂等。
"""
import json
import re
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
SRC = BASE_DIR.parent / '图片'
OUT = BASE_DIR / 'images-ready'
MANIFEST = BASE_DIR / 'images-manifest.json'

CATEGORIES = {
    'directional coupler': ('directional-coupler', 'Directional coupler'),
    'high frequency cable assembly': ('cable-assembly', 'High frequency cable assembly'),
    'hybrid coupler': ('hybrid-coupler', 'Hybrid coupler'),
    'indoor antenna': ('indoor-antenna', 'Indoor antenna'),
    'multi-band combiner': ('multi-band-combiner', 'Multi-band combiner'),
    'power splitter': ('power-splitter', 'Power splitter'),
    'termination load': ('termination-load', 'Termination load'),
    'waveguide': ('waveguide', 'Waveguide component'),
}

# 相机编号工厂实拍：按联系表逐张确认内容后填写
FACTORY_ALTS = {
    'P1026479_Moment': ('factory-cnc-turning', 'CNC turning with coolant for RF component machining'),
    'P1026469_Moment': ('factory-cnc-cavity-milling', 'CNC milling of an RF filter cavity'),
    'P1026470_Moment': ('factory-cnc-operator', 'Operator loading parts at a CNC machining center'),
    'P1026474_Moment': ('factory-machining-detail', 'Close-up of precision machining on a metal housing'),
    'P1026489_Moment': ('factory-vna-tuning-line', 'Technicians tuning RF filters with vector network analyzers'),
    'P1026514_Moment': ('factory-automated-assembly', 'Automated assembly machine for RF cavity filters'),
    'P1026515_Moment': ('factory-robotic-fastening', 'Automated fastening on an RF filter cavity plate'),
    'P1026517_Moment': ('factory-assembly-station', 'Technician working at an automated assembly station'),
    'P1026519_Moment': ('factory-production-line', 'RF component production line with automated equipment'),
    'P1026526_Moment': ('factory-manual-assembly', 'Manual assembly of an RF cavity filter housing'),
    'P1026538_Moment': ('factory-engineering-cad', 'Engineer reviewing a 2D engineering drawing'),
    'P1026539_Moment': ('factory-engineering-dfm', 'Engineer checking a machined part against its 3D CAD model'),
    'P1026561_Moment': ('factory-rf-testing', 'Technician testing an RF filter with bench instruments'),
    'P1080586_Moment': ('factory-machine-shop', 'Machine shop with CNC equipment and overhead crane'),
    'P1080601_Moment': ('factory-workshop-wide', 'Wide view of the SONNE assembly workshop'),
    'P1080609_Moment': ('factory-assembly-team', 'Assembly and testing team at work'),
}

ALTS = {
    'card-microwave': 'Microwave and RF components',
    'meeting-room-730679-1280-e1689057301283': 'Business meeting room',
    'part-cavity-silver': 'Silver plated RF filter cavity',
    'part-cover-raw': 'Machined cavity cover before surface treatment',
    'part-cavity-white': 'RF filter cavity housing',
    'prod-cabinet': 'Telecom enclosure cabinet',
    'prod-coupler-v2': 'RF directional coupler',
    'prod-hybrid': 'Hybrid coupler',
    'prod-bandpass-v2': 'RF bandpass filter',
    'prod-ceramic-filter-v2': 'Ceramic RF filter',
    'prod-combiner-v2': 'RF combiner',
    'prod-duplexer-v3': 'RF duplexer',
    'prod-n28-multiplexer': 'N28 multiplexer',
    'prod-ocu-combiner-v2': 'Outdoor combining unit',
    'prod-omt-v2': 'Ortho-mode transducer',
    'prod-tri-band-combiner': 'Tri-band RF combiner',
    'prod-tunable-filter-clean': 'Tunable RF filter',
    'tech-precision-machining': 'Precision CNC machining of high frequency parts',
    'tech-cat-tuning': 'Computer-aided tuning of RF filters',
    'chain-cnc-v2': 'CNC machining production line',
    'factory-assembly-detail': 'RF filter assembly detail',
    'factory-automation-detail': 'Automated assembly equipment detail',
    'factory-automation-line': 'Automated production line',
    'factory-building-v2': 'SONNE factory building',
    'factory-manual-line': 'Manual assembly line',
    'factory-robot-line': 'Robotic assembly line',
    'factory-test-rig': 'RF test rig',
    'factory-test-station': 'RF test station',
    'antenna-498438-1280': 'Base station antenna',
    'app-basestation-5g-site': '5G base station site',
    'app-low-altitude': 'Low-altitude communication application',
    'camera-775487-1280': 'Surveillance camera',
    'card-basestation': 'Base station RF infrastructure',
    'card-ibs': 'In-building wireless coverage',
    'cctv-1144371-1280': 'CCTV surveillance cameras',
    'insights-antenna-site-free-01': 'Antenna site for wireless infrastructure',
    'insights-base-station-tower-free-01': 'Base station tower with panel antennas',
    'insights-base-station-tower-free-02': 'Base station tower against the sky',
    'insights-base-station-tower': 'Macro base station tower',
    'insights-low-altitude-drone': 'Drone used in low-altitude communication',
    'market-datacenter': 'Data center infrastructure',
    'market-defense': 'Defense and public safety communication',
    'market-ftth': 'FTTH fiber access network',
    'radar-4502518-1280': 'Radar antenna system',
    'radar-7754760-1280': 'Radar installation',
    'satellite-693224-1280': 'Satellite earth station antenna',
}


NAME_OVERRIDES = {
    'antenna-498438-1280': 'base-station-antenna',
    'camera-775487-1280': 'surveillance-camera',
    'cctv-1144371-1280': 'cctv-surveillance-cameras',
    'radar-4502518-1280': 'radar-antenna-system',
    'radar-7754760-1280': 'radar-installation',
    'satellite-693224-1280': 'satellite-earth-station-antenna',
    'meeting-room-730679-1280-e1689057301283': 'meeting-room',
}


def slug(text):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text.lower())).strip('-')


def describe(src, rel):
    """返回 (输出名不含扩展, title, alt, usage)"""
    stem = src.stem
    parts = rel.parts
    if parts[0] == '01-Logo品牌':
        return 'logo-sonne-white', 'SONNE Electronics Logo (White)', 'SONNE Electronics logo', '品牌 Logo（反白版，深色背景用）'
    if stem in FACTORY_ALTS:
        name, alt = FACTORY_ALTS[stem]
        return name, alt, alt, '工厂实拍'
    if stem in ALTS:
        alt = ALTS[stem]
        return NAME_OVERRIDES.get(stem, slug(stem)), alt, alt, usage_of(parts)
    if parts[0] == '02-产品白底图' and len(parts) > 2 and stem.upper().startswith('SE-'):
        cat_slug, cat_title = CATEGORIES[parts[1]]
        model = stem.upper()
        name = f'{cat_slug}-{slug(stem)}'
        title = f'{cat_title} {model}'
        return name, title, f'SONNE {cat_title.lower()} {model}', f'产品白底图 - {parts[1]}'
    m = re.match(r'(power-splitter|directional-coupler)-(?:(\d)-way-)?(4-3-10|n)-female', slug(stem))
    if m:
        kind = 'power splitter' if m.group(1) == 'power-splitter' else 'directional coupler'
        way = f'{m.group(2)}-way ' if m.group(2) else ''
        conn = '4.3-10' if m.group(3) == '4-3-10' else 'N'
        alt = f'{way}{kind} with {conn} female connectors'
        return slug(stem), alt, alt, usage_of(parts)
    alt = slug(stem).replace('-', ' ')
    return slug(stem), alt, alt, usage_of(parts)


def usage_of(parts):
    if parts[0] == '02-产品白底图':
        return f'产品白底图 - {parts[1]}' if len(parts) > 2 else '产品白底图'
    if parts[0] == '03-产品场景图':
        return '应用/市场场景图'
    if parts[0] == '04-工厂车间':
        return '工厂/技术图'
    return '产品/技术示意图'


def convert(src, dst):
    with Image.open(src) as im:
        im.load()
        if dst.suffix == '.png':
            im.save(dst, optimize=True)
            return
        if im.mode == 'P':
            im = im.convert('RGBA')
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGB')
        if im.width > 1920:
            im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
        limit = 300 * 1024 if im.width >= 1800 else 200 * 1024
        for quality in (82, 75, 65, 55):
            im.save(dst, 'WEBP', quality=quality, method=6)
            if dst.stat().st_size <= limit:
                break
        else:
            if im.width > 1200:
                im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
                im.save(dst, 'WEBP', quality=72, method=6)


def main():
    OUT.mkdir(exist_ok=True)
    entries = []
    used = set()
    for src in sorted(SRC.rglob('*')):
        if not src.is_file() or src.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
            continue
        rel = src.relative_to(SRC)
        name, title, alt, usage = describe(src, rel)
        ext = '.png' if name.startswith('logo-') else '.webp'
        candidate = name
        n = 2
        while candidate in used:
            candidate = f'{name}-{n}'
            n += 1
        used.add(candidate)
        filename = candidate + ext
        dst = OUT / filename
        convert(src, dst)
        entries.append({
            'source': str(rel).replace('\\', '/'),
            'file': filename,
            'title': title,
            'alt': alt,
            'usage': usage,
            'width': Image.open(dst).width,
            'height': Image.open(dst).height,
            'bytes': dst.stat().st_size,
            'source_bytes': src.stat().st_size,
        })
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')
    total_src = sum(e['source_bytes'] for e in entries)
    total_out = sum(e['bytes'] for e in entries)
    print(f'共 {len(entries)} 张，原图 {total_src / 1048576:.1f}MB -> 规范化 {total_out / 1048576:.1f}MB')
    big = [e for e in entries if e['bytes'] > 200 * 1024]
    print(f'超过 200KB 的 {len(big)} 张（多为 1920px banner 允许 300KB）:')
    for e in big:
        print(f"  {e['file']} {e['width']}x{e['height']} {e['bytes'] // 1024}KB")
    unnamed = [e for e in entries if re.search(r'\d{5,}', e['alt'])]
    if unnamed:
        print('alt 仍含数字编号的:', [e['file'] for e in unnamed])


if __name__ == '__main__':
    main()
