"""Загрузка, фильтрация и статистика мирового справочника аэропортов."""
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
TYPES = {
    'large_airport': 'Крупный аэропорт', 'medium_airport': 'Средний аэропорт',
    'small_airport': 'Малый аэропорт', 'heliport': 'Вертодром',
    'seaplane_base': 'Гидроаэродром', 'balloonport': 'Аэростатная площадка',
    'closed': 'Закрытый объект',
}


def load_airports():
    meta = json.loads((ROOT / 'data/airports-meta.json').read_text(encoding='utf-8'))
    rows, invalid = [], 0
    with (ROOT / 'data/airports.csv').open(encoding='utf-8', newline='') as source:
        for row in csv.DictReader(source):
            try:
                lat, lon = float(row['latitude_deg']), float(row['longitude_deg'])
                if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError('Invalid coordinate')
            except (ValueError, TypeError):
                invalid += 1
                continue
            rows.append({
                'id': row['ident'], 'name': row['name'], 'type': row['type'],
                'lat': lat, 'lon': lon, 'country': row['iso_country'],
                'country_name': meta['countries'].get(row['iso_country'], row['iso_country']),
                'continent': row['continent'], 'city': row['municipality'],
                'scheduled': row['scheduled_service'] == 'yes',
                'iata': row['iata_code'], 'icao': row['icao_code'],
                '_search': ' '.join([row['ident'], row['name'], row['municipality'], row['iata_code'], row['icao_code'], row['keywords'], meta['countries'].get(row['iso_country'], '')]).casefold(),
            })
    rank = {'large_airport': 0, 'medium_airport': 1, 'small_airport': 2}
    rows.sort(key=lambda r: (rank.get(r['type'], 3), not bool(r['iata']), r['name']))
    meta['invalid_coordinates'] = invalid
    return rows, meta


def filter_airports(rows, query):
    scope = query.get('scope', 'world')
    country = query.get('country', '')
    kind = query.get('type', '')
    service = query.get('service', 'scheduled')
    search = query.get('q', '').strip().casefold()
    # Continents and country codes follow the source, not inferred political borders.
    return [r for r in rows
            if (scope == 'world' or (scope == 'EU' and r['continent'] == 'EU') or r['country'] == scope)
            and (not country or r['country'] == country)
            and (not kind or r['type'] == kind)
            and (service != 'scheduled' or (r['scheduled'] and r['type'] != 'closed'))
            and (service != 'open' or r['type'] != 'closed')
            and (not search or all(term in r['_search'] for term in search.split()))]


def response_for(rows, query):
    selected = filter_airports(rows, query)
    counts = Counter(r['country'] for r in selected)
    visible = selected[:6000]
    return {
        'total': len(selected), 'mapped': len(visible),
        'countries_count': len(counts),
        'scheduled_count': sum(r['scheduled'] and r['type'] != 'closed' for r in selected),
        'large_count': sum(r['type'] == 'large_airport' for r in selected),
        'types': dict(Counter(r['type'] for r in selected)),
        'top_countries': [{'code': code, 'name': next(r['country_name'] for r in selected if r['country'] == code), 'count': count} for code, count in counts.most_common(7)],
        'airports': [{k: v for k, v in r.items() if k != '_search'} for r in visible],
    }
