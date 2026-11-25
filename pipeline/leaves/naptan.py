"""Where each station is, from NaPTAN's national rail stops (area 910)"""

import csv
import xml.etree.ElementTree as ET

from .paths import DATA, stamp
from .sources import get

URL = 'https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml&atcoAreaCodes=910'
STATIONS = DATA / 'stations.csv'
NS = '{http://www.naptan.org.uk/}'


def fetch() -> int:
    with get(URL) as response:
        root = ET.parse(response).getroot()
    found = {}
    for stop in root.iter(NS + 'StopPoint'):
        crs = stop.findtext(f'.//{NS}AnnotatedRailRef/{NS}CrsRef')
        place = stop.find(f'{NS}Place/{NS}Location/{NS}Translation')
        if stop.get('Status') != 'active' or not crs or place is None:
            continue
        name = stop.findtext(f'{NS}Descriptor/{NS}CommonName').removesuffix(' Rail Station')
        lat, lon = (round(float(place.findtext(NS + k)), 5) for k in ('Latitude', 'Longitude'))
        found[crs] = (crs, name, lat, lon)
    with STATIONS.open('w', newline='') as fh:
        out = csv.writer(fh, lineterminator='\n')
        out.writerow(['crs', 'name', 'lat', 'lon'])
        out.writerows(sorted(found.values()))
    stamp('naptan')
    return len(found)


def load() -> dict[str, dict]:
    with STATIONS.open(newline='') as fh:
        return {row['crs']: row for row in csv.DictReader(fh)}
