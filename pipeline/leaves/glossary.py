"""Network Rail's attribution glossary, boiled down to the CSVs in data/glossary"""

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

from .paths import DATA

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
GLOSSARY = DATA / 'glossary'


def sheets(path: Path) -> dict[str, list[dict[str, str]]]:
    """Every sheet in a workbook as rows of {column letter: text}"""
    with zipfile.ZipFile(path) as book:
        strings = [
            ''.join(t.text or '' for t in item.iter(NS + 't'))
            for item in ET.fromstring(book.read('xl/sharedStrings.xml'))
        ]
        rels = ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))
        targets = {rel.get('Id'): rel.get('Target').lstrip('/') for rel in rels}
        out = {}
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).iter(NS + 'sheet'):
            target = targets[sheet.get(REL)]
            xml = ET.fromstring(book.read(target if target.startswith('xl/') else 'xl/' + target))
            out[sheet.get('name')] = [cells(row, strings) for row in xml.iter(NS + 'row')]
        return out


def cells(row: ET.Element, strings: list[str]) -> dict[str, str]:
    out = {}
    for cell in row.iter(NS + 'c'):
        value = cell.find(NS + 'v')
        if value is None:
            text = ''.join(t.text or '' for t in cell.iter(NS + 't'))
        else:
            text = strings[int(value.text)] if cell.get('t') == 's' else value.text
        out[re.match('[A-Z]+', cell.get('r')).group()] = text.strip()
    return out


def periods(rows: list[dict[str, str]]) -> list[tuple[str, str, str, int]]:
    """The Period Dates sheet: one block of columns per year, end dates as Excel serials"""
    head = next(row for row in rows if any(text.startswith('YEAR') for text in row.values()))
    years = {col: re.search(r'(\d{4})/(\d{2})', text) for col, text in head.items() if text}
    out = []
    for row in rows:
        number = re.fullmatch(r'Period (\d+)', row.get('A', ''))
        if not number:
            continue
        for col, year in years.items():
            date_col, days_col = shift(col, 2), shift(col, 4)
            if not row.get(date_col):
                continue
            end = date(1899, 12, 30) + timedelta(days=int(float(row[date_col])))
            days = int(row[days_col])
            start = end - timedelta(days=days - 1)
            pid = f'{year[1]}-{year[2]}-P{int(number[1]):02}'
            out.append((pid, start.isoformat(), end.isoformat(), days))
    return sorted(out)


def shift(col: str, by: int) -> str:
    n = 0
    for ch in col:
        n = n * 26 + ord(ch) - 64
    n += by
    out = ''
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def write(path: Path, header: list[str], rows) -> None:
    """Codes the workbook has since dropped stay, since older files still use them"""
    kept = {}
    if path.exists():
        with path.open(newline='') as fh:
            kept = {row[0]: tuple(row) for row in list(csv.reader(fh))[1:]}
    kept.update({row[0]: tuple(str(v) for v in row) for row in rows})
    with path.open('w', newline='') as fh:
        out = csv.writer(fh, lineterminator='\n')
        out.writerow(header)
        out.writerows(sorted(kept.values()))


def extract(xlsx: Path) -> None:
    """Rewrites data/glossary from a fresh copy of the workbook"""
    book = sheets(xlsx)
    GLOSSARY.mkdir(parents=True, exist_ok=True)
    stanox = {
        (r['A'].zfill(5), r.get('B', ''), r.get('C', ''), r.get('D', ''))
        for r in book['Stanox Codes'][1:]
        if r.get('A')
    }
    write(GLOSSARY / 'stanox.csv', ['stanox', 'name', 'crs', 'route'], stanox)
    reasons = {
        (r['B'], r.get('C', ''), r.get('E', ''), r.get('F', ''), r.get('G', ''))
        for r in book['Incident Reason'][1:]
        if r.get('B')
    }
    write(
        GLOSSARY / 'reasons.csv', ['code', 'name', 'description', 'category', 'supergroup'], reasons
    )
    managers = {
        (r['A'], r.get('C', ''), r.get('F', ''))
        for r in book['Responsible Manager'][1:]
        if r.get('A')
    }
    write(GLOSSARY / 'managers.csv', ['code', 'org', 'kind'], managers)
    write(
        GLOSSARY / 'periods.csv', ['period', 'start', 'end', 'days'], periods(book['Period Dates'])
    )


def load(name: str) -> list[dict[str, str]]:
    with (GLOSSARY / f'{name}.csv').open(newline='') as fh:
        return list(csv.DictReader(fh))
