import json
import re
import sys
import urllib.request

sys.path.insert(0, r'E:\qoder工作区\rf-sonne.com\generatepress-child')
import w

BAK = r'E:\qoder工作区\rf-sonne.com\generatepress-child\bak\hostinger-settings-backup-2026-10-27.json'


def call(path, method='GET', data=None):
    url = w.WP_DOMAIN + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=w._wp_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=w.REQUEST_TIMEOUT, context=w.SSL_CONTEXT) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')[:800]


def redact(obj):
    if isinstance(obj, dict):
        return {k: (f'<redacted len={len(v)}>' if re.search(r'bypass|token|secret|password|key', k, re.I) and isinstance(v, str) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


status, current = call('/wp-json/hostinger-tools-plugin/v1/get-settings')
print('BACKUP source status', status)
open(BAK, 'w', encoding='utf-8').write(json.dumps(redact(current), indent=2, ensure_ascii=False))
print('backup written (redacted), maintenance_mode =', current['data']['maintenance_mode'])

status, result = call('/wp-json/hostinger-tools-plugin/v1/update-settings', 'POST', {'maintenance_mode': False})
print('POST update-settings', status, json.dumps(redact(result), ensure_ascii=False)[:600])

status, after = call('/wp-json/hostinger-tools-plugin/v1/get-settings')
print('AFTER:', json.dumps(redact(after), indent=2, ensure_ascii=False)[:2000])
