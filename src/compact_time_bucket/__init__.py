"""Compact Time Bucket.

Groups timestamps into variable-length buckets for data aggregation.
"""

from .core import TimeBucketer, bucket_timestamps

__all__ = ["TimeBucketer", "bucket_timestamps"]
