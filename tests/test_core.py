"""Tests for compact_time_bucket.core."""

import math
import unittest

from compact_time_bucket import TimeBucketer, bucket_timestamps


class TimeBucketerConstructionTests(unittest.TestCase):
    def test_edges_are_sorted_and_finite(self):
        bucketer = TimeBucketer([1, 2, 3])
        self.assertEqual(bucketer.edges, (1.0, 2.0, 3.0))

    def test_edges_may_be_ints_or_floats(self):
        bucketer = TimeBucketer([0, 1.5, 10])
        self.assertEqual(bucketer.edges, (0.0, 1.5, 10.0))

    def test_empty_edges_are_rejected(self):
        with self.assertRaises(ValueError):
            TimeBucketer([])

    def test_unsorted_edges_are_rejected(self):
        with self.assertRaises(ValueError):
            TimeBucketer([3, 1])

    def test_duplicate_edges_are_rejected(self):
        with self.assertRaises(ValueError):
            TimeBucketer([1, 1])

    def test_infinite_edges_are_rejected(self):
        with self.assertRaises(ValueError):
            TimeBucketer([1, math.inf])

    def test_nan_edge_is_rejected(self):
        with self.assertRaises(ValueError):
            TimeBucketer([1, math.nan])


class TimeBucketerBucketForTests(unittest.TestCase):
    def setUp(self):
        self.bucketer = TimeBucketer([10, 20, 30])

    def test_timestamp_before_first_edge_goes_to_zero(self):
        self.assertEqual(self.bucketer.bucket_for(5), 0)

    def test_timestamp_equal_to_edge_goes_to_next_bucket(self):
        self.assertEqual(self.bucketer.bucket_for(10), 1)

    def test_timestamp_between_edges_goes_to_right_bucket(self):
        self.assertEqual(self.bucketer.bucket_for(25), 2)

    def test_timestamp_after_last_edge_goes_to_last_bucket(self):
        self.assertEqual(self.bucketer.bucket_for(100), 3)

    def test_timestamp_can_be_negative(self):
        self.assertEqual(self.bucketer.bucket_for(-5), 0)

    def test_float_timestamp_is_supported(self):
        self.assertEqual(self.bucketer.bucket_for(20.5), 2)

    def test_nan_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.bucketer.bucket_for(math.nan)


class TimeBucketerBucketManyTests(unittest.TestCase):
    def test_bucket_many_preserves_order(self):
        bucketer = TimeBucketer([1, 2, 3])
        self.assertEqual(
            bucketer.bucket_many([0, 1, 2, 3, 4]),
            [0, 1, 2, 3, 3],
        )

    def test_bucket_many_accepts_empty_sequence(self):
        bucketer = TimeBucketer([1])
        self.assertEqual(bucketer.bucket_many([]), [])


class BucketTimestampsFunctionTests(unittest.TestCase):
    def test_one_shot_function_matches_class(self):
        timestamps = [0, 5, 10, 15]
        edges = [5, 10]
        self.assertEqual(
            bucket_timestamps(timestamps, edges),
            TimeBucketer(edges).bucket_many(timestamps),
        )


if __name__ == "__main__":
    unittest.main()
