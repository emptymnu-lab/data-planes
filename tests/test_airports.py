import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from airports import filter_airports, load_airports, response_for
from app import make_handler


def airport(ident, country, continent, kind='large_airport', scheduled=True):
    return {'id': ident, 'country': country, 'country_name': country,
            'continent': continent, 'type': kind, 'scheduled': scheduled,
            'name': ident, '_search': ident.casefold()}


class AirportTests(unittest.TestCase):
    def setUp(self):
        self.rows = [airport('SVO Moscow', 'RU', 'EU'), airport('PEK Beijing', 'CN', 'AS'),
                     airport('JFK New York', 'US', 'NA'), airport('CDG Paris', 'FR', 'EU'),
                     airport('OLD Moscow', 'RU', 'EU', 'closed', True),
                     airport('SMALL Moscow', 'RU', 'EU', 'small_airport', False)]

    def test_default_excludes_closed_even_when_flagged_scheduled(self):
        self.assertEqual(len(filter_airports(self.rows, {})), 4)

    def test_combined_filters_and_case_insensitive_search(self):
        result = filter_airports(self.rows, {'scope': 'RU', 'q': 'sVo moscOW'})
        self.assertEqual([r['id'] for r in result], ['SVO Moscow'])
        self.assertEqual(filter_airports(self.rows, {'scope': 'RU', 'country': 'CN'}), [])

    def test_europe_uses_source_continent(self):
        self.assertEqual(len(filter_airports(self.rows, {'scope': 'EU'})), 2)

    def test_open_and_all_are_distinct(self):
        self.assertEqual(len(filter_airports(self.rows, {'service': 'open'})), 5)
        self.assertEqual(len(filter_airports(self.rows, {'service': 'all'})), 6)

    def test_empty_and_private_search_fields(self):
        result = response_for(self.rows, {'q': 'nothing'})
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['top_countries'], [])
        self.assertNotIn('_search', response_for(self.rows, {})['airports'][0])

    def test_map_cap_does_not_cap_statistics(self):
        rows = [airport(str(i), 'US', 'NA') for i in range(6002)]
        result = response_for(rows, {})
        self.assertEqual(result['total'], 6002)
        self.assertEqual(result['mapped'], 6000)
        self.assertEqual(result['large_count'], 6002)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler([]))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_real_data_filters_and_static_map(self):
        with urlopen(self.base + '/api/airports?scope=RU&q=SVO') as response:
            data = json.load(response)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['airports'][0]['iata'], 'SVO')
        with urlopen(self.base + '/world.geojson') as response:
            self.assertEqual(json.load(response)['type'], 'FeatureCollection')
        with urlopen(self.base + '/api/meta') as response:
            self.assertGreater(json.load(response)['source_rows'], 80000)


if __name__ == '__main__':
    unittest.main()
