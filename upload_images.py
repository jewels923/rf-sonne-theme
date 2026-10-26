#!/usr/bin/env python3
"""按 images-manifest.json 上传 images-ready/ 到 WP 媒体库，写入 alt/title，并登记 images.md。
可重复运行：已成功的图片自动跳过，失败的可单独重跑。
"""
import concurrent.futures
import json
import threading
import time
from pathlib import Path

import w

BASE_DIR = Path(__file__).resolve().parent
READY = BASE_DIR / 'images-ready'
MANIFEST = BASE_DIR / 'images-manifest.json'
LOG = BASE_DIR / 'images-upload-log.json'
IMAGES_MD = BASE_DIR / 'images.md'

_lock = threading.Lock()


def load_log():
    return json.loads(LOG.read_text(encoding='utf-8')) if LOG.exists() else {}


def save(entry_file, record, log):
    with _lock:
        log[entry_file] = record
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')


def process(entry, log):
    path = READY / entry['file']
    result = None
    last = None
    for attempt in range(4):
        try:
            result, status = w.wp_api_upload(path)
            break
        except Exception as e:
            last = e
            print(f"  上传重试 {entry['file']} ({attempt + 1}/4): {str(e)[:120]}", flush=True)
            time.sleep(2 * (attempt + 1))
    if result is None:
        return entry['file'], {'error': f'upload: {last}'}

    record = {'id': result['id'], 'url': result['source_url']}
    for attempt in range(3):
        try:
            w.wp_api_patch(f"/media/{result['id']}", {'alt_text': entry['alt'], 'title': entry['title']})
            break
        except Exception as e:
            record['error'] = f'meta: {e}'
            time.sleep(2)
    else:
        return entry['file'], record
    record.pop('error', None)
    return entry['file'], record


def write_images_md(manifest, log):
    lines = [
        '# SONNE 图片清单（rf-sonne.com 媒体库）',
        '',
        '| 文件名 | Title | Alt | URL | 用途/场景 |',
        '|--------|-------|-----|-----|-----------|',
    ]
    for e in manifest:
        rec = log.get(e['file'], {})
        url = rec.get('url', '上传失败：' + rec.get('error', '未上传'))
        lines.append(f"| {e['file']} | {e['title']} | {e['alt']} | {url} | {e['usage']} |")
    IMAGES_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    log = load_log()
    todo = [e for e in manifest if not (log.get(e['file'], {}).get('url') and 'error' not in log[e['file']])]
    print(f'总数 {len(manifest)}，已完成 {len(manifest) - len(todo)}，本次上传 {len(todo)}', flush=True)
    if todo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(process, e, log): e for e in todo}
            done = 0
            for fut in concurrent.futures.as_completed(futures):
                entry = futures[fut]
                filename, record = fut.result()
                save(filename, record, log)
                done += 1
                mark = 'OK ' if record.get('url') and 'error' not in record else 'FAIL'
                print(f"[{done}/{len(todo)}] {mark} {filename} {record.get('url', record.get('error', ''))}", flush=True)
    write_images_md(manifest, load_log())
    failed = {k: v for k, v in load_log().items() if 'error' in v or 'url' not in v}
    print(f'\n完成。失败 {len(failed)} 张。清单: {IMAGES_MD}')
    for k, v in failed.items():
        print(' ', k, v)


if __name__ == '__main__':
    main()
