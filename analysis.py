"""Чистые функции анализа: их можно изучать без веб-сервера."""
import csv
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).parent / 'data' / 'flights.csv'


def number(value):
    """В открытых данных NA означает отсутствие измерения, а не ноль."""
    return None if value in ('', 'NA', None) else float(value)


def load_flights(path=DATA):
    with open(path, encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        for key in ('dep_delay', 'arr_delay', 'air_time', 'distance'):
            row[key] = number(row[key])
        row['month'] = int(row['month'])
    return rows


def summarize(rows):
    measured = [r['arr_delay'] for r in rows if r['arr_delay'] is not None]
    groups = defaultdict(list)
    for row in rows:
        if row['arr_delay'] is not None:
            groups[row['carrier']].append(row['arr_delay'])
    return {
        'total': len(rows),
        'measured': len(measured),
        'missing': len(rows) - len(measured),
        'mean_delay': round(sum(measured) / len(measured), 1) if measured else None,
        'delayed_percent': round(100 * sum(d > 15 for d in measured) / len(measured), 1) if measured else None,
        'carriers': [
            {'name': name, 'delay': round(sum(values) / len(values), 1), 'count': len(values)}
            for name, values in sorted(groups.items())
        ],
        'destinations': [{'name': name, 'count': count} for name, count in Counter(r['dest'] for r in rows).most_common(10)],
    }
