import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
PERIODS = DATA / 'periods'
STATIC = ROOT / 'static'


def stamp(source: str, changed: bool = True) -> None:
    """Notes the day a source last changed, for the method page's register"""
    path = DATA / 'taken.json'
    taken = json.loads(path.read_text()) if path.exists() else {}
    if changed or source not in taken:
        taken[source] = date.today().isoformat()
        path.write_text(json.dumps(dict(sorted(taken.items())), indent=1) + '\n')
