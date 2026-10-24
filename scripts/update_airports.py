"""Обновить локальный снимок OurAirports: python3 scripts/update_airports.py."""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/'
FIELDS = ['ident', 'type', 'name', 'latitude_deg', 'longitude_deg', 'continent',
          'iso_country', 'municipality', 'scheduled_service', 'icao_code', 'iata_code', 'keywords']


def prepare(airports, countries):
    rows = list(csv.DictReader(io.StringIO(airports.decode('utf-8-sig'))))
    country_rows = list(csv.DictReader(io.StringIO(countries.decode('utf-8-sig'))))
    if not rows or not set(FIELDS).issubset(rows[0]):
        raise ValueError('Неожиданный формат airports.csv')
    if not country_rows or not {'code', 'name'}.issubset(country_rows[0]):
        raise ValueError('Неожиданный формат countries.csv')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows({key: row[key] for key in FIELDS} for row in rows)
    metadata = {
        'source': 'OurAirports', 'source_url': BASE + 'airports.csv',
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'sha256_airports': hashlib.sha256(airports).hexdigest(),
        'sha256_countries': hashlib.sha256(countries).hexdigest(),
        'source_rows': len(rows),
        'countries': {row['code']: row['name'] for row in country_rows},
    }
    return output.getvalue(), metadata


if __name__ == '__main__':
    # Download and validate both files before replacing the local data.
    with urlopen(BASE + 'airports.csv', timeout=90) as response:
        airports = response.read()
    with urlopen(BASE + 'countries.csv', timeout=90) as response:
        countries = response.read()
    text, metadata = prepare(airports, countries)
    (ROOT / 'data' / 'airports.csv').write_text(text, encoding='utf-8')
    (ROOT / 'data' / 'airports-meta.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Сохранено {metadata['source_rows']} записей")
