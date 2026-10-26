#!/usr/bin/env python3
"""SEO TDK 批量同步（按 docs/SEO_SYNC_WORKFLOW.md）

从策略 MD 提取 **URL 路径 / **SEO Title / **Meta Description / **Focus Keyphrase
（实际格式为全角冒号），经 SEO Bridge 写入 Yoast 字段，再 read 回读验证。
用法: python seo_sync.py [--dry-run]
"""
import json
import re
import ssl
import sys
import base64
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
STRATEGY_DIR = BASE_DIR.parent / '网站' / 'kjbath.wxkntest.com' / '框架与内容策略' / '02-页面内容策略'

# --- 从 w.py 提取凭证（单一来源） ---
_w = (BASE_DIR / 'w.py').read_text(encoding='utf-8')
DOMAIN = re.search(r"WP_DOMAIN\s*=\s*'([^']+)'", _w).group(1)
USER = re.search(r"WP_USERNAME\s*=\s*'([^']+)'", _w).group(1)
PWD = re.search(r"WP_APP_PASSWORD\s*=\s*'([^']+)'", _w).group(1)
AUTH = 'Basic ' + base64.b64encode(f'{USER}:{PWD}'.encode()).decode()

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

YOAST = {
    'title': '_yoast_wpseo_title',
    'desc': '_yoast_wpseo_metadesc',
    'kw': '_yoast_wpseo_focuskw',
}


def api(method, url, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': AUTH,
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'seo-sync/1.0',
    })
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read())


def extract(md_path):
    text = md_path.read_text(encoding='utf-8')
    def grab(label):
        # 兼容 **URL 路径：** / **URL 路径**: 两种冒号位置
        m = re.search(rf'\*\*\s*{label}\s*[：:]?\s*\*\*\s*[：:]?\s*(.+)', text)
        return m.group(1).strip().strip('`').strip() if m else None
    return {
        'url': grab(r'URL 路径'),
        'title': grab(r'SEO Title'),
        'desc': grab(r'Meta Description'),
        'kw': grab(r'Focus Keyphrase'),
        'file': md_path.name,
    }


def norm(path):
    p = urlparse(path).path if path.startswith('http') else path
    p = '/' + p.strip('/')
    return p


def main():
    dry = '--dry-run' in sys.argv

    pages = api('GET', f'{DOMAIN}/wp-json/wp/v2/pages?per_page=100&status=publish&_fields=id,link')
    path2id = {}
    for p in pages:
        path2id[norm(p['link'])] = p['id']
    print(f'线上 publish 页面: {len(pages)} 个\n')

    rows = []
    for md in sorted(STRATEGY_DIR.glob('*.md')):
        info = extract(md)
        if not info['url']:
            rows.append((info['file'], '-', '-', '跳过: 无 URL 路径字段'))
            continue
        key = norm(info['url'])
        pid = path2id.get(key)
        if not pid:
            rows.append((info['file'], info['url'], '-', '跳过: 线上找不到该路径'))
            continue
        missing = [k for k in ('title', 'desc', 'kw') if not info[k]]
        if missing:
            rows.append((info['file'], info['url'], pid, f'跳过: 缺字段 {missing}'))
            continue
        rows.append((info['file'], info['url'], pid, 'OK', info))

    todo = [r for r in rows if len(r) == 5]
    for r in rows:
        if len(r) != 5:
            print(f'  [{r[3]}] {r[0]} ({r[1]})')
    print(f'\n待同步: {len(todo)} 页')
    if dry:
        for r in todo:
            print(f'  [DRY] {r[0]} -> id={r[2]}')
        return

    ok = fail = 0
    for fname, url, pid, _, info in todo:
        payload = {'meta': {
            YOAST['title']: info['title'],
            YOAST['desc']: info['desc'],
            YOAST['kw']: info['kw'],
        }}
        try:
            api('POST', f'{DOMAIN}/wp-json/seo-bridge/v1/update/{pid}', payload)
            # 回读验证
            back = api('GET', f'{DOMAIN}/wp-json/seo-bridge/v1/read/{pid}')
            meta = back.get('seo_meta', {})
            got_title = meta.get(YOAST['title'])
            got_kw = meta.get(YOAST['kw'])
            got_desc = meta.get(YOAST['desc'])
            if isinstance(got_title, list):
                got_title = got_title[0] if got_title else None
            if got_title == info['title'] and got_kw == info['kw'] and (got_desc == info['desc'] if isinstance(got_desc, str) else True):
                print(f'  ✅ {fname} (id={pid})')
                ok += 1
            else:
                print(f'  ⚠️  {fname} (id={pid}) 回读不一致: title={got_title!r} kw={got_kw!r}')
                fail += 1
        except urllib.error.HTTPError as e:
            print(f'  ❌ {fname} (id={pid}) HTTP {e.code}: {e.read()[:150]}')
            fail += 1
        except Exception as e:
            print(f'  ❌ {fname} (id={pid}) {e}')
            fail += 1
    print(f'\n完成: 成功 {ok}，失败 {fail}')


if __name__ == '__main__':
    main()
