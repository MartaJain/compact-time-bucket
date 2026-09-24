# Compact Time Bucket

Compact Time Bucket groups timestamps into variable-length buckets for data aggregation.

```python
from compact_time_bucket import TimeBucketer

bucketer = TimeBucketer([10, 30, 60])
print(bucketer.bucket_for(25))  # 1
print(bucketer.bucket_many([5, 10, 30, 61]))  # [0, 1, 2, 3]
```

The bucket edges are right-inclusive: a timestamp equal to an edge falls into the next bucket. Timestamps before the first edge go to bucket 0, and timestamps after the last edge go to the last bucket. Buckets are therefore always defined, and aggregation code never has to check for a missing bucket.

## Why this exists

Aggregating event data often requires grouping timestamps into intervals. Fixed-width buckets are simple but waste space when activity is uneven: a quiet hour needs the same storage as a busy one. Variable-length buckets let you put boundaries where the data changes, not where the clock says to. The trade-off made here is that the bucketer stores only bucket edges and returns integer indices. It does not store bucket contents, labels, or metadata. That keeps it small and predictable, and leaves those concerns to the caller.

## Awkward edge

Bucket edges must be finite and strictly increasing. An empty edge list is rejected because there would be no meaningful bucket index to return. NaN timestamps are also rejected; a NaN cannot be placed in any bucket, and silently returning a bucket would hide a data problem.
