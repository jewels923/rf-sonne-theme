#!/usr/bin/env python3

# ============================================================
# 配置
# ============================================================

WP_DOMAIN = 'https://rf-sonne.com'
WP_USERNAME = 'jewels923'
SYNC_API_URL = f'{WP_DOMAIN}/wp-content/themes/generatepress-child/trans.php'
# 密码与 token 不在此文件中：环境变量 WP_APP_PASSWORD / SYNC_AUTH_TOKEN 优先，
# 否则读取同目录 w.secrets.json（见 BASE_DIR 下方的加载逻辑）。


"""WordPress 站点管理工具 — 统一 CLI

用法:
  python w.py upload <file_path>          上传文件到服务器
  python w.py download <file_path>        从服务器下载文件
  python w.py create <title> <slug> [parent]  创建 WordPress 内容
  python w.py create-term <taxonomy> <name> [slug] [parent]  创建分类法分类

create 命令参数说明:
  - title:       标题
  - slug:        别名（URL 路径）
  - parent:      父级 ID（可选，默认 0）
  - --type:      文章类型（默认 page，可选 post、product 等）
  - 示例: python w.py create "关于我们" about-us
  - 示例: python w.py create --type=posts "最新动态" latest-news
  - 示例: python w.py create --type=products "产品A" product-a
  python w.py pull [target]               拉取页面内容到本地
  python w.py push <slug> [slug2 ...]     推送本地内容到 WordPress（支持批量）
  python w.py image <file_path>           上传图片到 WordPress 媒体库
  python w.py pages                       获取所有页面列表 -> pages.json
  python w.py media                       获取所有媒体文件列表 -> uploaded_images.json
  python w.py pull-files                  拉取服务器主题文件到本地（自动发现全部文件）
  python w.py pull-files --dry-run        仅列出服务器文件，不下载

create-term 命令参数说明:
  - taxonomy:    分类法名称，如 category、product-category、tag 等
  - name:        分类名称
  - slug:        分类别名（可选，不传则自动从 name 生成）
  - parent:      父分类 ID（可选，默认 0）
  - 示例: python w.py create-term product-category "男士服装" mens-clothing
  - 示例: python w.py create-term category "新闻" news

pull 命令参数说明:
  - 无参数:        拉取全部页面（先更新 pages.json，再逐个拉取）
  - slug 名称:     拉取指定 slug 的页面，ID 从 pages.json 获取
                  例: python w.py pull blogs
  - 完整 URL:      取路径最后一段作为 slug，ID 从 pages.json 获取
                  例: python w.py pull https://example.com/blogs/

push 命令参数说明:
  - 支持批量推送:  可传入一个或多个 slug，从 pages.json 获取 ID
                  例: python w.py push blogs
                  例: python w.py push blogs faq about-us

pull-files 命令参数说明:
  - 无参数:         递归列出并下载主题目录下所有文件到本地
  - --dry-run:     仅列出服务器上的文件，不实际下载
"""

import argparse
import base64
import concurrent.futures
import http.client
import datetime
import json
import mimetypes
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BAK_DIR = BASE_DIR / 'bak'
MAX_BAK_KEEP = 10  # 保留最近 10 次备份目录

SECRETS_FILE = BASE_DIR / 'w.secrets.json'
_secrets = json.loads(SECRETS_FILE.read_text(encoding='utf-8')) if SECRETS_FILE.exists() else {}
WP_DOMAIN = os.environ.get('WP_DOMAIN', WP_DOMAIN)
WP_USERNAME = os.environ.get('WP_USERNAME', WP_USERNAME)
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD') or _secrets.get('app_password', '')
SYNC_AUTH_TOKEN = os.environ.get('SYNC_AUTH_TOKEN') or _secrets.get('sync_auth_token', '')
SYNC_API_URL = f'{WP_DOMAIN}/wp-content/themes/generatepress-child/trans.php'

MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒
REQUEST_TIMEOUT = 40  # 秒
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
MAX_CONCURRENT = 5  # 默认并发数
SKIP_DIRS = {'node_modules', '.git', '.svn', '__pycache__', '.idea', '.vscode', 'bak'}
SKIP_FILES = {'trans.log'}
PAGE_FILE_ALIASES = {
    'hospitality': 'hospitality-solutions',
    'residential': 'residential-solutions',
    'commercial': 'commercial-solutions',
    'australia-waterview-beach-apartment': 'case-australia',
    'canada-maguire-apartment': 'case-canada',
    'tanzania-commercial-office-doors': 'case-tanzania',
    'shower-door-drop-test': 'blog-drop-test',
    'shower-hardware-salt-spray-test': 'blog-salt-spray-test',
    'sgcc-ce-certified-shower-glass': 'blog-sgcc-ce',
}

# ============================================================
# HTTP 工具函数
# ============================================================

def _create_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        # Windows 证书库可能含过期交叉签名导致默认校验误报证书过期，
        # 因此用 certifi 的 CA 包；未安装时显式降级并提示，而非静默关闭校验。
        print('警告: 未安装 certifi，已跳过证书校验。请执行: python -m pip install certifi', file=sys.stderr)
        return ssl._create_unverified_context()


SSL_CONTEXT = _create_ssl_context()


def _wp_auth():
    return 'Basic ' + base64.b64encode(f'{WP_USERNAME}:{WP_APP_PASSWORD}'.encode()).decode()


def _wp_headers(content_type='application/json'):
    return {
        'Content-Type': content_type,
        'Authorization': _wp_auth(),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }


class WpApiError(Exception):
    def __init__(self, message, status=None, body=''):
        super().__init__(message)
        self.status = status
        self.body = body


def _retry_request(req, retries=MAX_RETRIES, delay=RETRY_DELAY):
    """仅网络错误与 429/5xx 重试；4xx 属于请求本身的问题，直接抛出"""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            if e.code in RETRYABLE_HTTP_STATUS and attempt < retries - 1:
                print(f'  HTTP {e.code}，{delay}秒后重试 ({attempt + 1}/{retries})...', file=sys.stderr, flush=True)
                time.sleep(delay)
                continue
            raise WpApiError(f'HTTP {e.code}', status=e.code, body=body) from e
        except (OSError, http.client.HTTPException) as e:
            # 覆盖 URLError / SSLError / TimeoutError / RemoteDisconnected 等
            reason = getattr(e, 'reason', e)
            if attempt < retries - 1:
                print(f'  网络错误: {reason}，{delay}秒后重试 ({attempt + 1}/{retries})...', file=sys.stderr, flush=True)
                time.sleep(delay)
                continue
            raise WpApiError(f'网络错误: {reason}') from e
    return None


def wp_api_get(endpoint, params=None):
    url = f'{WP_DOMAIN}/wp-json/wp/v2{endpoint}'
    if params:
        from urllib.parse import urlencode
        url += '?' + urlencode(params)
    req = urllib.request.Request(url, headers=_wp_headers())
    return _retry_request(req)


def wp_api_post(endpoint, data):
    url = f'{WP_DOMAIN}/wp-json/wp/v2{endpoint}'
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=_wp_headers(), method='POST')
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise WpApiError(f'HTTP {e.code}', status=e.code, body=body) from e
    except (OSError, http.client.HTTPException) as e:
        raise WpApiError(f'网络错误: {getattr(e, "reason", e)}') from e


def wp_api_patch(endpoint, data):
    url = f'{WP_DOMAIN}/wp-json/wp/v2{endpoint}'
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=_wp_headers(), method='PATCH')
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise WpApiError(f'HTTP {e.code}', status=e.code, body=body) from e
    except (OSError, http.client.HTTPException) as e:
        raise WpApiError(f'网络错误: {getattr(e, "reason", e)}') from e


def wp_api_upload(file_path):
    mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
    filename = file_path.name
    image_data = file_path.read_bytes()

    boundary = '----WebKitFormBoundary' + __import__('secrets').token_hex(16)
    body_parts = [
        f'--{boundary}'.encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
        f'Content-Type: {mime_type}'.encode(),
        b'',
        image_data,
        f'--{boundary}--'.encode(),
        b'',
    ]
    body = b'\r\n'.join(body_parts)

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Authorization': _wp_auth(),
        'Content-Disposition': f'attachment; filename="{filename}"',
        'User-Agent': 'WordPress-Media-Uploader/1.0',
    }
    url = f'{WP_DOMAIN}/wp-json/wp/v2/media'
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=300, context=SSL_CONTEXT) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise WpApiError(f'上传失败: HTTP {e.code}', status=e.code, body=body) from e
    except (OSError, http.client.HTTPException) as e:
        raise WpApiError(f'网络错误: {getattr(e, "reason", e)}') from e


class SyncError(Exception):
    pass


def sync_request(payload):
    payload['token'] = SYNC_AUTH_TOKEN
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(SYNC_API_URL, data=data, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'SyncClient/2.0',
    }, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CONTEXT) as resp:
            raw = resp.read()
            if not raw:
                raise SyncError(f'服务器返回空响应 (HTTP {resp.status})')
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                snippet = raw[:500].decode('utf-8', errors='replace')
                raise SyncError(f'服务器返回非 JSON 响应 (HTTP {resp.status})\n原始响应: {snippet}')
            if not result.get('success'):
                raise SyncError(result.get('error', '未知错误'))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        msg = f'HTTP {e.code}'
        if body:
            msg += f'\n响应内容: {body[:500]}'
        raise SyncError(msg)
    except urllib.error.URLError as e:
        raise SyncError(f'网络错误: {e.reason}')
    except SyncError:
        raise
    except Exception as e:
        raise SyncError(str(e))


# ============================================================
# 辅助函数
# ============================================================

BOM = '﻿'


def remove_bom(text):
    if text.startswith(BOM):
        return text[1:]
    return text


def normalize_content(raw):
    content = remove_bom(raw)
    content = content.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '')
    content = content.replace('\r', '')
    content = re.sub(r'\n{2,}', '\n', content)
    content = content.strip()
    return f'<!-- wp:html -->\n{content}\n<!-- /wp:html -->'


def validate_html_fragment(content):
    lower = content.lower()
    if '<html' in lower or '<body' in lower:
        raise ValueError('内容包含 <html> 或 <body> 标签，请使用纯 HTML 片段')


def format_size(size_bytes):
    if size_bytes >= 1048576:
        return f'{size_bytes / 1048576:.2f} MB'
    if size_bytes >= 1024:
        return f'{size_bytes / 1024:.2f} KB'
    return f'{size_bytes} B'


def resolve_image_path(input_str):
    base_dir = BASE_DIR.resolve()
    input_str = str(input_str).replace('\\', '/')

    # 绝对路径
    if input_str[0] in ('/', '\\') or (len(input_str) > 1 and input_str[1] == ':'):
        resolved = Path(input_str).resolve()
        if not str(resolved).startswith(str(base_dir)):
            print('错误: 文件必须在项目目录下', file=sys.stderr)
            sys.exit(1)
        if resolved.exists():
            return resolved
        print(f'错误: 文件不存在: {input_str}', file=sys.stderr)
        sys.exit(1)

    candidate = BASE_DIR / input_str
    if candidate.exists():
        return candidate.resolve()

    # 无扩展名，尝试推断
    if candidate.suffix == '':
        for ext in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
            test = Path(str(candidate) + '.' + ext)
            if test.exists():
                return test.resolve()

    print(f'错误: 文件不存在: {input_str}', file=sys.stderr)
    sys.exit(1)


def normalize_path(input_path):
    """标准化文件路径：去除 .\\ 或 ./ 前缀，统一为正斜杠"""
    p = str(input_path)
    # 去除 .\ 或 ./ 前缀
    if p.startswith('.\\') or p.startswith('./'):
        p = p[2:]
    # 反斜杠转正斜杠
    p = p.replace('\\', '/')
    return p


def _get_bak_timestamp_dir():
    """获取当前时间戳的备份目录"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    return BAK_DIR / timestamp


def _clean_old_bak():
    """清理旧备份目录，保留最近 MAX_BAK_KEEP 个"""
    if not BAK_DIR.exists():
        return
    bak_dirs = sorted(
        [d for d in BAK_DIR.iterdir() if d.is_dir()],
        key=lambda x: x.name,
        reverse=True
    )
    for old_dir in bak_dirs[MAX_BAK_KEEP:]:
        try:
            import shutil
            shutil.rmtree(old_dir)
            print(f'  清理旧备份: {old_dir.name}')
        except Exception as e:
            print(f'  清理失败: {old_dir.name} - {e}', file=sys.stderr)


def _backup_file(file_path, bak_dir):
    """备份单个文件到指定备份目录"""
    if not file_path.exists():
        return False
    try:
        rel_path = file_path.relative_to(BASE_DIR)
    except ValueError:
        print(f'  备份跳过（路径不在项目目录内）: {file_path}', file=sys.stderr)
        return False
    bak_path = bak_dir / rel_path
    bak_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import shutil
        shutil.copy2(file_path, bak_path)
        return True
    except Exception as e:
        print(f'  备份失败: {rel_path} - {e}', file=sys.stderr)
        return False


def _backup_files(file_paths, bak_dir):
    """批量备份文件，返回成功备份的数量"""
    if not file_paths:
        return 0
    bak_dir.mkdir(parents=True, exist_ok=True)
    success = 0
    for fp in file_paths:
        if _backup_file(fp, bak_dir):
            success += 1
    return success


def _sync_list_dir(path):
    """递归列出目录下所有文件（通过 trans.php list_files）"""
    try:
        result = sync_request({'action': 'list_files', 'path': path})
    except SyncError as e:
        print(f'  警告: 列出目录失败 {path}: {e}', file=sys.stderr)
        return []
    files = []
    for item in result.get('data', []):
        name = item['name']
        # 跳过隐藏文件/目录，但保留 .htaccess 和 .trae
        if name.startswith('.') and name not in ('.htaccess', '.trae'):
            continue
        if item['type'] == 'directory':
            if name in SKIP_DIRS:
                continue
            files.extend(_sync_list_dir(path + '/' + name))
        else:
            if name in SKIP_FILES:
                continue
            files.append({
                'path': path + '/' + name,
                'size': item.get('size') or 0,
            })
    return files


# ============================================================
# 命令实现
# ============================================================

def cmd_upload(args):
    """上传文件到服务器"""
    file_path = normalize_path(args.file_path)
    local_path = BASE_DIR / file_path
    if not local_path.exists():
        print(f'错误: 本地文件不存在: {file_path}', file=sys.stderr)
        sys.exit(1)

    content = local_path.read_text(encoding='utf-8')
    backup = not getattr(args, 'no_backup', False)
    try:
        sync_request({
            'action': 'write_file',
            'path': './' + file_path,
            'content': content,
            'backup': backup,
        })
    except SyncError as e:
        print(f'同步请求失败: {e}', file=sys.stderr)
        sys.exit(1)
    print(f'已上传: {file_path}')


def cmd_download(args):
    """从服务器下载文件"""
    file_path = normalize_path(args.file_path)
    local_path = BASE_DIR / file_path

    # 备份现有文件（除非指定 --no-backup）
    if not args.no_backup and local_path.exists():
        bak_dir = _get_bak_timestamp_dir()
        print(f'备份: {file_path} -> bak/{bak_dir.name}/')
        _backup_file(local_path, bak_dir)

    try:
        result = sync_request({
            'action': 'read_file',
            'path': './' + file_path,
        })
    except SyncError as e:
        print(f'同步请求失败: {e}', file=sys.stderr)
        sys.exit(1)

    local_path.parent.mkdir(parents=True, exist_ok=True)

    data = result['data']
    content = data['content']
    if data.get('encoding') == 'base64':
        import base64 as b64
        local_path.write_bytes(b64.b64decode(content))
    else:
        local_path.write_text(content, encoding='utf-8')
    print(f'已下载: {file_path}')


def cmd_create(args):
    """创建 WordPress 内容（页面、文章、自定义文章类型）"""
    # post_type 到 REST API 端点的映射
    endpoint_map = {
        'page': 'pages',
        'post': 'posts',
    }
    post_type = args.type or 'page'
    endpoint = endpoint_map.get(post_type, post_type)  # 自定义类型直接用传入值
    title = args.title
    slug = args.slug
    parent = args.parent

    result, status = wp_api_post(f'/{endpoint}', {
        'title': title,
        'slug': slug,
        'parent': parent,
        'status': 'publish',
        'content': '',
    })
    if status == 201:
        print(f'创建成功!')
        print(f'  ID:       {result["id"]}')
        print(f'  类型:     {post_type}')
        print(f'  标题:     {result["title"]["rendered"]}')
        print(f'  Slug:     {result["slug"]}')
        print(f'  链接:     {result["link"]}')
    else:
        print(f'创建失败: HTTP {status}', file=sys.stderr)
        if isinstance(result, dict) and 'message' in result:
            print(f'  错误信息: {result["message"]}', file=sys.stderr)
        sys.exit(1)


def cmd_create_term(args):
    """创建分类法分类"""
    taxonomy = args.taxonomy
    name = args.name
    slug = args.slug
    parent = args.parent

    # 如果没有提供 slug，从 name 自动生成
    if not slug:
        # 简单的 slug 生成：转为小写，空格替换为连字符，移除特殊字符
        slug = name.lower().replace(' ', '-').replace('_', '-')
        slug = re.sub(r'[^\w\-]', '', slug)

    data = {
        'name': name,
        'slug': slug,
    }
    if parent:
        data['parent'] = parent

    result, status = wp_api_post(f'/{taxonomy}', data)

    if status == 201:
        print(f'分类创建成功!')
        print(f'  分类 ID: {result["id"]}')
        print(f'  名称:    {result["name"]}')
        print(f'  Slug:    {result["slug"]}')
        print(f'  分类法:  {taxonomy}')
        if result.get('parent', 0):
            print(f'  父分类:  {result["parent"]}')
    else:
        print(f'创建失败: HTTP {status}', file=sys.stderr)
        if isinstance(result, dict) and 'message' in result:
            print(f'  错误信息: {result["message"]}', file=sys.stderr)
        sys.exit(1)


def _load_pages_json():
    path = BASE_DIR / 'pages.json'
    if not path.exists():
        print('错误: pages.json 不存在，请先运行 python w.py pages', file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding='utf-8'))


def _find_page(slug):
    pages = _load_pages_json()
    for p in pages:
        if p['slug'] == slug:
            return p
    print(f'错误: 在 pages.json 中未找到 slug="{slug}" 的页面', file=sys.stderr)
    raise LookupError(f'未找到 slug="{slug}"，请先运行 python w.py pages')


def _get_local_page_path(slug):
    """
    根据 slug 获取本地 HTML 文件路径
    如果 slug 是 home_2（WP 上的首页别名），强制映射到本地的 home.html
    """
    if slug == 'home_2':
        local_filename = 'home'
    else:
        local_filename = PAGE_FILE_ALIASES.get(slug, slug)
    return BASE_DIR / 'website' / f'{local_filename}.html'


def _resolve_target(target):
    if not target:
        return None

    target = target.strip()

    if target.startswith('http://') or target.startswith('https://'):
        from urllib.parse import urlparse
        parsed = urlparse(target)
        slug = parsed.path.rstrip('/').split('/')[-1]
        if not slug:
            print(f'错误: 无法从 URL 中提取 slug: {target}', file=sys.stderr)
            sys.exit(1)
        return slug

    return target


def _pull_one(slug, bak_dir=None):
    page_info = _find_page(slug)
    page_id = page_info['id']
    file_path = _get_local_page_path(slug)

    result = wp_api_get(f'/pages/{page_id}', {'context': 'edit'})

    api_slug = result.get('slug', '')
    api_link = result.get('link', '')

    if api_slug != slug:
        print(f'\n数据不一致，已停止!', file=sys.stderr)
        print(f'  pages.json 中: slug="{slug}"', file=sys.stderr)
        print(f'  API 返回:     slug="{api_slug}"', file=sys.stderr)
        raise ValueError(f'slug 不一致: {slug}')

    json_url = page_info.get('url', '')
    if json_url and api_link and json_url.rstrip('/') != api_link.rstrip('/'):
        print(f'\nURL 不一致警告:', file=sys.stderr)
        print(f'  pages.json: {json_url}', file=sys.stderr)
        print(f'  API 返回:   {api_link}', file=sys.stderr)
        raise ValueError(f'URL 不一致: {slug}')

    print(f'  [{slug}] ID={page_id} | {result["title"]["rendered"]} | {result["modified"]}')

    content = result.get('content', {}).get('raw', '')
    content = remove_bom(content)

    # 备份现有文件
    if bak_dir is not False and file_path.exists():
        actual_bak_dir = bak_dir if bak_dir else _get_bak_timestamp_dir()
        actual_bak_dir.mkdir(parents=True, exist_ok=True)
        _backup_file(file_path, actual_bak_dir)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f'  -> {file_path} ({len(content)} 字节)')
    return True


def cmd_pull(args):
    """拉取页面内容到本地"""
    target = getattr(args, 'target', None)
    no_backup = getattr(args, 'no_backup', False)

    if not target:
        print('正在更新 pages.json ...')
        cmd_pages(args)
        print()

        pages = _load_pages_json()
        print(f'开始拉取 {len(pages)} 个页面 ...\n')

        # 创建备份目录（除非指定 --no-backup）
        bak_dir = False if no_backup else _get_bak_timestamp_dir()
        if bak_dir:
            bak_dir.mkdir(parents=True, exist_ok=True)
            print(f'备份目录: bak/{bak_dir.name}/\n')

        success = 0
        failed = []
        for p in pages:
            try:
                if _pull_one(p['slug'], bak_dir):
                    success += 1
            except Exception as e:
                failed.append(p['slug'])
                print(f'  错误: 拉取 {p["slug"]} 失败 - {e}', file=sys.stderr)

        print(f'\n完成: {success}/{len(pages)} 个页面已保存到 website/ 目录')
        if not no_backup:
            _clean_old_bak()
        if failed:
            print(f'失败: {", ".join(failed)}', file=sys.stderr)
            sys.exit(1)
        return

    slug = _resolve_target(target)
    # 单个拉取也需要备份（除非指定 --no-backup），且只备份一次
    file_path = _get_local_page_path(slug)
    bak_dir = False
    if not no_backup and file_path.exists():
        bak_dir = _get_bak_timestamp_dir()
        print(f'备份: website/{file_path.name} -> bak/{bak_dir.name}/')
        bak_dir.mkdir(parents=True, exist_ok=True)
        _backup_file(file_path, bak_dir)

    print(f'拉取页面: slug="{slug}"')
    _pull_one(slug, bak_dir)


def _push_one(slug):
    page_info = _find_page(slug)
    page_id = page_info['id']
    file_path = _get_local_page_path(slug)
    api_url = f'/pages/{page_id}'

    print(f'页面 ID: {page_id} (来自 pages.json)')
    print(f'Slug:    {slug}')
    print(f'文件路径: {file_path}')

    if not file_path.exists():
        raise FileNotFoundError(f'本地文件不存在: {file_path}')

    content = file_path.read_text(encoding='utf-8')
    if content.startswith('﻿'):
        print('检测到 UTF-8 BOM，已移除')
        content = content[1:]

    print(f'内容大小: {len(content)} 字节')
    validate_html_fragment(content)

    content = normalize_content(content)
    print('已规范化内容并添加 wp:html 标记')

    print('发送请求到 WordPress API...')
    result, status = wp_api_post(api_url, {'content': content})
    print('更新成功!')
    print(f'页面标题: {result["title"]["rendered"]}')
    print(f'更新时间: {result["modified"]}')
    print()


def cmd_push(args):
    """推送本地内容到 WordPress：单个失败不中断，最后统一返回非零"""
    failed = []
    for slug in args.slugs:
        try:
            _push_one(slug)
        except Exception as e:
            failed.append(slug)
            detail = getattr(e, 'body', '') or str(e)
            print(f'  推送失败 [{slug}]: {detail[:500]}', file=sys.stderr)
    if failed:
        print(f'\n失败 {len(failed)}/{len(args.slugs)}: {", ".join(failed)}', file=sys.stderr)
        sys.exit(1)


def cmd_pull_files(args):
    """拉取服务器主题目录下所有文件到本地"""
    print('正在获取文件列表...')
    all_files = _sync_list_dir('./')

    if not all_files:
        print('未发现任何文件')
        return

    total = len(all_files)
    total_size = sum(f['size'] for f in all_files)
    print(f'发现 {total} 个文件，总大小 {format_size(total_size)}')

    if args.dry_run:
        print()
        for f in sorted(all_files, key=lambda x: x['path']):
            print(f'  {f["path"]} ({format_size(f["size"])})')
        return

    no_backup = getattr(args, 'no_backup', False)

    # 收集需要备份的现有文件
    def _name_from_path(p):
        """去掉 ./ 或 .// 前缀作为本地相对路径"""
        # 循环去掉所有 ./ 前缀（处理 ./ 或 .// 等情况）
        while p.startswith('./'):
            p = p[2:]
        # 去掉开头的 /
        if p.startswith('/'):
            p = p[1:]
        return p

    def _local_from_remote(p):
        # 服务器返回的路径不可信，写盘前必须确认仍落在项目目录内
        local = (BASE_DIR / _name_from_path(p)).resolve()
        if not local.is_relative_to(BASE_DIR):
            raise ValueError(f'路径越出项目目录，已拒绝: {p}')
        return local

    existing_files = []
    for finfo in all_files:
        try:
            local_path = _local_from_remote(finfo['path'])
        except ValueError as e:
            print(f'  跳过: {e}', file=sys.stderr)
            continue
        if local_path.exists():
            existing_files.append(local_path)

    # 备份现有文件（除非指定 --no-backup）
    if not no_backup and existing_files:
        bak_dir = _get_bak_timestamp_dir()
        bak_dir.mkdir(parents=True, exist_ok=True)
        bak_count = _backup_files(existing_files, bak_dir)
        print(f'\n备份 {bak_count}/{len(existing_files)} 个现有文件到 bak/{bak_dir.name}/')

    print(f'\n开始下载 (并发数: {MAX_CONCURRENT}) ...\n')

    success = 0
    failed = []

    def download_one(finfo):
        path = finfo['path']
        try:
            result = sync_request({'action': 'read_file', 'path': path})
            local_path = _local_from_remote(path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            data = result['data']
            content = data['content']
            if data.get('encoding') == 'base64':
                import base64 as b64
                local_path.write_bytes(b64.b64decode(content))
            else:
                local_path.write_text(content, encoding='utf-8')
            return (path, True, None)
        except Exception as e:
            return (path, False, str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {executor.submit(download_one, f): f['path'] for f in all_files}
        for future in concurrent.futures.as_completed(futures):
            path, ok, err = future.result()
            if ok:
                success += 1
                print(f'  OK  {_name_from_path(path)} ({format_size(next((f["size"] for f in all_files if f["path"] == path), 0))})')
            else:
                failed.append((path, err))
                print(f'  FAIL  {path}: {err}')

    # 重试
    retry_round = 1
    while failed and retry_round <= 3:
        print(f'\n=== 重试失败的文件 (第 {retry_round} 次) ===\n')
        retry_failed = []
        retry_files = [{'path': p, 'size': 0} for p, _ in failed]
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            futures = {executor.submit(download_one, f): f['path'] for f in retry_files}
            for future in concurrent.futures.as_completed(futures):
                path, ok, err = future.result()
                if ok:
                    success += 1
                    print(f'  重试成功: {_name_from_path(path)}')
                else:
                    retry_failed.append((path, err))
        failed = retry_failed
        retry_round += 1

    print()
    print(f'===== 拉取完成 =====')
    print(f'  总计:   {total}')
    print(f'  成功:   {success}')
    print(f'  失败:   {len(failed)}')
    if failed:
        print('\n  最终失败列表:')
        for path, reason in failed:
            print(f'    - {_name_from_path(path)}: {reason}')

    if not no_backup:
        _clean_old_bak()


def cmd_image(args):
    """上传图片到 WordPress 媒体库"""
    file_path = resolve_image_path(args.file_path)
    result, status = wp_api_upload(file_path)
    if status == 201:
        media_id = result["id"]
        source_url = result["source_url"]
        print(f'上传成功!')
        print(f'  媒体 ID: {media_id}')
        print(f'  URL:     {source_url}')
        if args.alt:
            filename = file_path.stem
            title = filename.replace('-', ' ').replace('_', ' ').title()
            update_data = {"alt_text": args.alt, "title": title}
            wp_api_patch(f'/media/{media_id}', update_data)
            print(f'  Alt:     {args.alt}')
            print(f'  Title:   {title}')
        else:
            print(f'  Alt:     {result.get("alt_text", "")}')
    else:
        print(f'上传失败: HTTP {status}', file=sys.stderr)
        sys.exit(1)


def cmd_pages(_args):
    """获取所有页面列表 → pages.json"""
    pages = []
    seen_ids = set()
    page = 1
    while True:
        try:
            batch = wp_api_get('/pages', {
                'per_page': 20,
                'page': page,
                'status': 'publish,draft',
                'context': 'edit',
                '_fields': 'id,title,slug,link',
            })
        except WpApiError as e:
            # 总数恰好是 20 的倍数时，WP 对越界页返回 400 而非空数组
            if e.status == 400 and 'rest_post_invalid_page_number' in e.body:
                break
            raise
        new_pages = [p for p in batch if p['id'] not in seen_ids]
        seen_ids.update(p['id'] for p in new_pages)
        pages.extend(new_pages)
        # CDN 可能把不同 page 参数缓存成同一页，无新 id 时终止以免死循环
        if len(batch) < 20 or not new_pages:
            break
        page += 1

    result = []
    for p in pages:
        result.append({
            'id': p['id'],
            'title': p.get('title', {}).get('raw', ''),
            'slug': p.get('slug', ''),
            'url': p.get('link', ''),
        })

    output = BASE_DIR / 'pages.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Done. {len(result)} 个页面已保存到 {output}')


def cmd_media(_args):
    """获取所有媒体文件列表 → uploaded_images.json"""
    all_media = []
    page = 1
    per_page = 100

    print('开始获取媒体文件...\n')

    while True:
        media = wp_api_get('/media', {'per_page': per_page, 'page': page})
        count = len(media)
        print(f'第 {page} 页: 获取到 {count} 个文件')

        for item in media:
            all_media.append({
                'id': item['id'],
                'url': item['source_url'],
                'alt': item.get('alt_text', ''),
                'desc': '',
            })

        if count < per_page:
            break
        page += 1

    output = BASE_DIR / 'uploaded_images.json'
    output.write_text(json.dumps(all_media, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n总计: {len(all_media)} 个媒体文件')
    print(f'已保存到: {output}')


# ============================================================
# CLI 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog='w.py',
        description='WordPress 站点管理工具',
        epilog='示例:\n'
               '  python w.py upload functions.py\n'
               '  python w.py download style.css\n'
               '  python w.py pull blogs              # 按 slug 拉取\n'
               '  python w.py pull https://example.com/blogs/  # 按 URL 拉取\n'
               '  python w.py pull                    # 拉取全部页面\n'
               '  python w.py push blogs              # 按 slug 推送\n'
               '  python w.py create "About Us" about-us\n'
               '  python w.py create --type=post "最新动态" latest-news\n'
               '  python w.py create -t product "产品A" product-a\n'
               '  python w.py create-term product-category "男士服装" mens-clothing\n'
               '  python w.py create-term category "新闻" news\n'
               '  python w.py image photo.jpg\n'
               '  python w.py pages\n'
               '  python w.py media\n'
               '  python w.py pull-files              # 拉取主题文件\n'
               '  python w.py pull-files --dry-run    # 仅列出文件\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # upload
    p = subparsers.add_parser('upload', help='上传文件到服务器')
    p.add_argument('file_path', help='要上传的文件路径')
    p.add_argument('--no-backup', action='store_true', help='不备份服务器端文件')

    # download
    p = subparsers.add_parser('download', help='从服务器下载文件')
    p.add_argument('file_path', help='要下载的文件路径（相对于主题根目录）')
    p.add_argument('--no-backup', action='store_true', help='不备份本地文件')

    # create
    p = subparsers.add_parser('create', help='创建 WordPress 内容（页面、文章、自定义文章类型）')
    p.add_argument('title', help='标题')
    p.add_argument('slug', help='别名（URL 路径）')
    p.add_argument('parent', nargs='?', default=0, type=int, help='父级 ID（默认 0）')
    p.add_argument('--type', '-t', default='page', help='文章类型（page/post/product 等，默认 page）')

    # create-term
    p = subparsers.add_parser('create-term', help='创建分类法分类')
    p.add_argument('taxonomy', help='分类法名称，如 category、product-category、tag')
    p.add_argument('name', help='分类名称')
    p.add_argument('slug', nargs='?', default=None, help='分类别名（可选，不传则自动生成）')
    p.add_argument('parent', nargs='?', default=0, type=int, help='父分类 ID（默认 0）')

    # pull
    p = subparsers.add_parser('pull', help='拉取页面内容到本地')
    p.add_argument('target', nargs='?', default=None,
                   help='slug 名称 / 完整 URL（可选，不传则拉取全部页面）')
    p.add_argument('--no-backup', action='store_true', help='不备份本地文件')

    # push
    p = subparsers.add_parser('push', help='推送本地内容到 WordPress')
    p.add_argument('slugs', nargs='+', help='页面别名（从 pages.json 获取 ID，支持多个）')

    # image
    p = subparsers.add_parser('image', help='上传图片到 WordPress 媒体库')
    p.add_argument('file_path', help='图片文件路径（支持无扩展名自动推断）')
    p.add_argument('--alt', default=None, help='设置 alt 文本（title 从文件名自动推导）')

    # pages
    subparsers.add_parser('pages', help='获取所有页面列表 → pages.json')

    # media
    subparsers.add_parser('media', help='获取所有媒体文件列表 → uploaded_images.json')

    # pull-files
    p = subparsers.add_parser('pull-files', help='拉取服务器主题文件到本地（自动发现全部文件）')
    p.add_argument('--dry-run', action='store_true', help='仅列出文件，不下载')
    p.add_argument('--no-backup', action='store_true', help='不备份本地文件')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'upload': cmd_upload,
        'download': cmd_download,
        'create': cmd_create,
        'create-term': cmd_create_term,
        'pull': cmd_pull,
        'push': cmd_push,
        'image': cmd_image,
        'pages': cmd_pages,
        'media': cmd_media,
        'pull-files': cmd_pull_files,
    }

    if not WP_APP_PASSWORD:
        print('错误: 缺少应用密码。请设置环境变量 WP_APP_PASSWORD，或在 w.secrets.json 中填写 app_password',
              file=sys.stderr)
        sys.exit(1)
    if args.command in ('upload', 'download', 'pull-files') and not SYNC_AUTH_TOKEN:
        print('错误: 缺少同步 token。请设置环境变量 SYNC_AUTH_TOKEN，或在 w.secrets.json 中填写 sync_auth_token',
              file=sys.stderr)
        sys.exit(1)

    try:
        commands[args.command](args)
    except WpApiError as e:
        print(f'错误: {e}', file=sys.stderr)
        if e.body:
            print(e.body[:500], file=sys.stderr)
        sys.exit(1)
    except (LookupError, ValueError, FileNotFoundError, SyncError) as e:
        print(f'错误: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
