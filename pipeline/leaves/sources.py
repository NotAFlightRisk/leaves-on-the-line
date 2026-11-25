"""Where period files come from: Azure Blob containers, listed and hashed before they're trusted"""

import hashlib
import json
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .paths import DATA

# Network Rail's old public bucket, 2018-19 P01 to 2023-24 P09 and nothing since
PUBLIC = 'https://sacuksprodnrdigital0001.blob.core.windows.net/historic-delay-attribution'
MANIFEST = DATA / 'sources.json'
AGENT = {'User-Agent': 'leaves-on-the-line (+https://leaves.peng.ly)'}


@dataclass(frozen=True)
class Blob:
    container: str
    name: str
    size: int
    etag: str

    @property
    def key(self) -> str:
        return f'{self.container}/{self.name}'


def split(url: str) -> tuple[str, str]:
    base, _, sas = url.partition('?')
    return base.rstrip('/'), sas


def get(url: str):
    return urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=120)


def listing(url: str, container: str) -> Iterator[Blob]:
    """Every zip in a container, a page of the List Blobs API at a time"""
    base, sas = split(url)
    marker = ''
    while True:
        params = ['restype=container&comp=list', sas, marker and f'marker={quote(marker)}']
        query = '&'.join(p for p in params if p)
        with get(f'{base}?{query}') as response:
            page = ET.parse(response).getroot()
        for blob in page.iter('Blob'):
            name = blob.findtext('Name')
            if name.lower().endswith('.zip'):
                props = blob.find('Properties')
                yield Blob(
                    container,
                    name,
                    int(props.findtext('Content-Length')),
                    props.findtext('Etag') or '',
                )
        marker = page.findtext('NextMarker') or ''
        if not marker:
            return


def download(url: str, blob: Blob, folder: Path) -> tuple[Path, str]:
    """Fetches a blob (or reuses a copy of the same size) and returns its path and sha256"""
    base, sas = split(url)
    path = folder / blob.name.replace('/', '_')
    if not path.exists() or path.stat().st_size != blob.size:
        quoted = quote(blob.name)
        with (
            get(f'{base}/{quoted}' + (f'?{sas}' if sas else '')) as response,
            path.open('wb') as fh,
        ):
            shutil.copyfileobj(response, fh)
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return path, digest.hexdigest()


def manifest() -> dict[str, dict]:
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def save_manifest(entries: dict[str, dict]) -> None:
    MANIFEST.write_text(json.dumps(dict(sorted(entries.items())), indent=1) + '\n')
