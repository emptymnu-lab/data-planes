import unittest

from analysis import number, summarize


class AnalysisTests(unittest.TestCase):
    def test_missing_and_negative_delays(self):
        rows = [
            {'carrier': 'AA', 'dest': 'LAX', 'arr_delay': -10},
            {'carrier': 'AA', 'dest': 'LAX', 'arr_delay': 20},
            {'carrier': 'BB', 'dest': 'SFO', 'arr_delay': None},
            {'carrier': 'AA', 'dest': 'SFO', 'arr_delay': 15},
        ]
        result = summarize(rows)
        self.assertEqual(result['total'], 4)
        self.assertEqual(result['measured'], 3)
        self.assertEqual(result['missing'], 1)
        self.assertEqual(result['mean_delay'], 8.3)
        self.assertEqual(result['delayed_percent'], 33.3)
        self.assertEqual(result['carriers'], [{'name': 'AA', 'delay': 8.3, 'count': 3}])

    def test_empty_selection(self):
        result = summarize([])
        self.assertIsNone(result['mean_delay'])
        self.assertIsNone(result['delayed_percent'])
        self.assertEqual(result['destinations'], [])

    def test_missing_is_not_zero(self):
        self.assertIsNone(number('NA'))
        self.assertEqual(number('0'), 0)


if __name__ == '__main__':
    unittest.main()
