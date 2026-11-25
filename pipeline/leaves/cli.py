"""leaves: fetch, roll up, check and publish Network Rail's delay attribution files"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

from . import codes, glossary, naptan, orr, rollup, site, sources
from .paths import PERIODS, stamp

# Network Rail publishes six to ten weeks after a period ends, so past this something's broken
STALE_DAYS = 70


def say(text: str) -> None:
    print(text, flush=True)


def digest(folder: Path) -> str:
    """What a staged period holds, so two copies of one release can be told apart"""
    sha = hashlib.sha256()
    for table in ('places', 'sections'):
        sha.update((folder / f'{table}.csv.gz').read_bytes())
    return sha.hexdigest()


def stage(job: tuple[str, str, str, str]) -> list[dict]:
    """Rolls every period in one file into its own folder, for ingest to pick from"""
    name, path, sha, folder = job
    out = []
    with zipfile.ZipFile(path) as book:
        for number, member in enumerate(book.namelist()):
            if not member.lower().endswith('.csv'):
                continue
            when = rollup.released(name, book, member)
            for period, roll in rollup.roll(book, member).items():
                dest = Path(folder) / sha[:16] / f'{number}-{period}'
                source = {'file': name, 'csv': member, 'released': when, 'sha256': sha}
                info = rollup.save(roll, source, dest)
                cells = {op: dict(by) for op, by in orr.cells(roll.orr).items()}
                out.append(
                    {
                        'period': period,
                        'dir': str(dest),
                        'released': when,
                        'sha256': sha,
                        'content': digest(dest),
                        'agreed': info['file_agreed'],
                        'cells': cells,
                    }
                )
    return out


def installed(period: str) -> tuple[str, str]:
    path = PERIODS / period / 'meta.json'
    if not path.exists():
        return '', ''
    source = json.loads(path.read_text())['source']
    return source['released'], source.get('content', '')


def newest(staged: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """The latest release of each period, refusing to guess between two different copies of it"""
    best, clashes = {}, []
    for period in sorted({item['period'] for item in staged}):
        items = [item for item in staged if item['period'] == period]
        top = max(item['released'] for item in items)
        latest = {item['content']: item for item in items if item['released'] == top}
        if len(latest) > 1:
            clashes.append(
                f'{period}: {len(latest)} different files all say they are the {top} release'
            )
        else:
            best[period] = next(iter(latest.values()))
    return best, clashes


def ingest(
    url: str,
    container: str,
    cache: Path,
    *,
    backfill: bool,
    force: bool,
    accept: bool,
    workers: int,
) -> list[str]:
    known = sources.manifest()
    jobs, blobs = [], {}
    for blob in sources.listing(url, container):
        entry = known.get(blob.key)
        if not force and entry and (entry['size'], entry['etag']) == (blob.size, blob.etag):
            continue
        path, sha = sources.download(url, blob, cache)
        say(f'📥 {blob.name} ({blob.size / 1e6:.0f} MB)')
        jobs.append((blob.name, str(path), sha, str(cache / 'stage')))
        blobs[blob.name] = {'key': blob.key, 'size': blob.size, 'etag': blob.etag, 'sha256': sha}
    if not jobs:
        say('Nothing new')
        return []
    with ProcessPoolExecutor(workers) as pool:
        staged = [item for batch in pool.map(stage, jobs) for item in batch]
    table = orr.table()
    results = [(s['cells'], table.get(s['period'], {}), s['agreed']) for s in staged]
    policy = orr.build_policy(results) if backfill else json.loads(orr.POLICY.read_text())
    if backfill:
        orr.POLICY.write_text(json.dumps(policy, indent=1) + '\n')
    best, errors = newest(staged)
    failed = {item['sha256'] for item in staged if item['period'] not in best}
    for period, item in best.items():
        released, content = installed(period)
        older = item['released'] < released
        same = (item['released'], item['content']) == (released, content)
        if not force and (older or same):
            say(f'⏭️ {period}: already have the {released} release')
            continue
        theirs = table.get(period)
        problems = orr.check(item['cells'], theirs, item['agreed'], policy) if theirs else None
        if problems and not (backfill or accept):
            errors += [f'{period}: {p}' for p in problems]
            failed.add(item['sha256'])
            continue
        install(item, problems)
        stamp('network-rail')
        flag = '✅' if problems == [] else '➖' if problems is None else '⚠️'
        say(
            f'{flag} {period} released {item["released"]}, {item["agreed"]:.1%} agreed'
            + (f': {"; ".join(problems)}' if problems else '')
        )
    for blob in blobs.values():
        if blob['sha256'] not in failed:
            periods = sorted({s['period'] for s in staged if s['sha256'] == blob['sha256']})
            known[blob.pop('key')] = {**blob, 'periods': periods}
    sources.save_manifest(known)
    return errors


def staleness() -> list[str]:
    newest = max(p.name for p in PERIODS.iterdir() if (p / 'meta.json').exists())
    ended = date.fromisoformat(codes.calendar()[newest]['end'])
    days = (date.today() - ended).days
    return [f'the newest period, {newest}, ended {days} days ago'] if days > STALE_DAYS else []


def install(item: dict, problems: list[str] | None) -> None:
    dest = PERIODS / item['period']
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(item['dir'], dest)
    meta = json.loads((dest / 'meta.json').read_text())
    meta['source']['content'] = item['content']
    meta['orr'] = {'checked': problems is not None, 'problems': problems or []}
    (dest / 'meta.json').write_text(json.dumps(meta, indent=1) + '\n')


def report(errors: list[str]) -> None:
    """Problems go to Bugsink when there's a DSN, and fail the run either way"""
    if not errors:
        return
    for error in errors:
        say(f'❌ {error}')
    if os.environ.get('SENTRY_DSN'):
        import sentry_sdk

        sentry_sdk.capture_message('\n'.join(errors), level='error')
        sentry_sdk.flush()
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog='leaves', description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('glossary', help='rewrite data/glossary').add_argument('xlsx', type=Path)
    commands.add_parser('naptan', help='refresh station locations')
    commands.add_parser('orr', help="refresh ORR's Table 3184")
    for name in ('backfill', 'update'):
        cmd = commands.add_parser(name, help=f'{name} periods from a Blob container')
        cmd.add_argument('--cache', type=Path, help='keep downloads here')
        cmd.add_argument('--force', action='store_true', help='roll up files already seen')
        cmd.add_argument(
            '--accept', action='store_true', help='install periods that fail the ORR check'
        )
        cmd.add_argument('--workers', type=int, default=2)
    commands.add_parser('site', help='write the JSON and CSVs the site is built from')
    args = parser.parse_args()

    if os.environ.get('SENTRY_DSN'):
        import sentry_sdk

        sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], send_default_pii=False, traces_sample_rate=0)

    if args.command == 'glossary':
        glossary.extract(args.xlsx)
    elif args.command == 'naptan':
        say(f'📍 {naptan.fetch():,} stations')
    elif args.command == 'orr':
        say(f'📊 {orr.fetch():,} ORR rows')
    elif args.command == 'site':
        report(site.build())
    else:
        url = sources.PUBLIC if args.command == 'backfill' else os.environ.get('LEAVES_DROP', '')
        if not url:
            say('No LEAVES_DROP container set, so nothing to update')
            return
        backfill = args.command == 'backfill'
        with tempfile.TemporaryDirectory() as scratch:
            cache = args.cache or Path(scratch)
            (cache / 'stage').mkdir(parents=True, exist_ok=True)
            errors = ingest(
                url,
                'public' if backfill else 'drop',
                cache,
                backfill=backfill,
                force=args.force,
                accept=args.accept,
                workers=args.workers,
            )
        # a drop that's never delivered anything isn't stale, it's just not hooked up yet
        delivered = any(key.startswith('drop/') for key in sources.manifest())
        report(errors + (staleness() if delivered and not backfill else []))
