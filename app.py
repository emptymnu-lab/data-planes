"""Запуск: python3 app.py. Внешние библиотеки не требуются."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from analysis import load_flights, summarize

ROOT = Path(__file__).parent


def make_handler(rows):
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == '/api/flights':
                query = parse_qs(url.query)
                selected = rows
                for field in ('origin', 'carrier', 'month'):
                    value = query.get(field, [''])[0]
                    if value:
                        selected = [r for r in selected if str(r[field]) == value]
                result = summarize(selected)
                result['options'] = {field: sorted({r[field] for r in rows}) for field in ('origin', 'carrier', 'month')}
                body = json.dumps(result, ensure_ascii=False, allow_nan=False).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()
    return partial(Handler, directory=str(ROOT / 'static'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Учебная аналитика авиарейсов')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(load_flights()))
    print(f'Flight Lab: http://{args.host}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
