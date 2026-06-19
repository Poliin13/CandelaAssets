#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

RAW_BASE = 'https://raw.githubusercontent.com/Poliin13/CandelaAssets/master/'
OLD_URL_RE = re.compile(r'raw\.githubusercontent\.com/Poliin13/[^/]+/[0-9a-f]{7,40}/')
MEDIA_EXTS = {'.pdf', '.gif', '.webp', '.png', '.jpg', '.jpeg', '.mp4'}
URL_KEYS = {
    'url', 'pdfLink', 'pdfUrl', 'htmlLink', 'image', 'image2', 'image_url',
    'imageName_1', 'imageName_2', 'imageName_3', 'imageName_4', 'chapterIcon',
    'profilePic', 'ytVideo',
}


def iter_json_files(root: Path, all_json: bool):
    if all_json:
        for path in sorted(root.rglob('*.json')):
            if '.git' not in path.parts:
                yield path
        return

    production = [root / 'assets/List_Books.json', root / 'assets/ContributorsList.json']
    seen = set()
    while production:
        path = production.pop(0).resolve()
        if path in seen or not path.exists():
            continue
        seen.add(path)
        yield path
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        child_urls = []
        walk(data, path, child_urls)
        for _, url in child_urls:
            if url.startswith(RAW_BASE):
                rel = unquote(url[len(RAW_BASE):])
                if rel.lower().endswith('.json'):
                    production.append(root / rel)


def walk(value, source: Path, urls: list[tuple[Path, str]], key: str | None = None):
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            walk(child_value, source, urls, child_key)
    elif isinstance(value, list):
        for child in value:
            walk(child, source, urls, key)
    elif isinstance(value, str):
        if value.startswith('http') and (key in URL_KEYS or 'raw.githubusercontent.com' in value):
            urls.append((source, value))


def format_size(size: int) -> str:
    units = ['B', 'KB', 'MB', 'GB']
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f'{value:.1f} {unit}'
        value /= 1024
    return f'{size} B'


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate CandelaAssets production data and media links.')
    parser.add_argument('--root', default='.', help='CandelaAssets repo root')
    parser.add_argument('--large-mb', type=float, default=10.0, help='Large media threshold in MB')
    parser.add_argument('--all-json', action='store_true', help='Validate every JSON file, including legacy/staging files')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    urls: list[tuple[Path, str]] = []
    json_count = 0

    for path in iter_json_files(root, args.all_json):
        json_count += 1
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception as exc:
            errors.append(f'JSON parse failed: {path.relative_to(root)}: {exc}')
            continue
        walk(data, path, urls)

    for source, url in urls:
        rel_source = source.relative_to(root)
        if 'CandelaPics' in url:
            errors.append(f'Old CandelaPics URL in {rel_source}: {url}')
        if OLD_URL_RE.search(url):
            errors.append(f'Commit-hash raw URL in {rel_source}: {url}')
        if url.startswith(RAW_BASE):
            rel = unquote(url[len(RAW_BASE):])
            target = root / rel
            if not target.exists():
                errors.append(f'Missing file for URL in {rel_source}: {rel}')
        elif 'raw.githubusercontent.com/Poliin13/CandelaAssets/' in url:
            parsed = urlparse(url)
            errors.append(f'Unexpected CandelaAssets raw base in {rel_source}: {parsed.path}')

    ds_store = [p.relative_to(root) for p in root.rglob('.DS_Store') if '.git' not in p.parts]
    if ds_store:
        errors.append(f'.DS_Store files present: {len(ds_store)}')
        warnings.extend(f'  {p}' for p in ds_store[:20])
        if len(ds_store) > 20:
            warnings.append(f'  ... {len(ds_store) - 20} more')

    media_by_ext: Counter[str] = Counter()
    media_size_by_ext: defaultdict[str, int] = defaultdict(int)
    large_files: list[tuple[int, Path]] = []
    threshold = int(args.large_mb * 1024 * 1024)
    for path in root.rglob('*'):
        if not path.is_file() or '.git' in path.parts:
            continue
        ext = path.suffix.lower()
        if ext in MEDIA_EXTS:
            size = path.stat().st_size
            media_by_ext[ext] += 1
            media_size_by_ext[ext] += size
            if size >= threshold:
                large_files.append((size, path.relative_to(root)))

    print('CandelaAssets validation')
    print(f'Root: {root}')
    print(f'JSON files parsed: {json_count}' + (' (all JSON)' if args.all_json else ' (production graph)'))
    print(f'URLs discovered: {len(urls)}')
    print('\nMedia summary:')
    for ext, total_size in sorted(media_size_by_ext.items(), key=lambda item: item[1], reverse=True):
        print(f'  {ext:6} {media_by_ext[ext]:5d} {format_size(total_size):>10}')

    if large_files:
        print(f'\nLarge media files >= {args.large_mb:.1f} MB:')
        for size, path in sorted(large_files, reverse=True)[:30]:
            print(f'  {format_size(size):>10}  {path}')

    if warnings:
        print('\nWarnings:')
        for warning in warnings:
            print(warning)

    if errors:
        print('\nErrors:')
        for error in errors:
            print(f'  - {error}')
        return 1

    print('\nOK: JSON and raw asset links are valid.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
