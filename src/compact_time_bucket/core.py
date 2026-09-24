"""Core bucketing logic for Compact Time Bucket.

The design centres on a single class, TimeBucketer, which takes a sequence of
buckets expressed as half-open intervals in seconds. Timestamps are mapped to
the bucket that contains them, or to a sentinel bucket when they fall before
or after all configured buckets.

The word "compact" reflects the storage model: a bucketer keeps only the bucket
boundaries and assigns each timestamp to an integer bucket index. The caller
can use that index to aggregate data without materialising a full time series.
"""

from bisect import bisect_right
from dataclasses import dataclass
from numbers import Real
from typing import Iterable, List, Sequence, Tuple, Union


Timestamp = Union[int, float]


@dataclass(frozen=True)
class TimeBucketer:
    """Assign timestamps to variable-length buckets.

    Buckets are defined by an ordered sequence of right edges. If the edges are
    ``[e0, e1, ..., en]`` then the buckets are::

        (-inf, e0]   -> bucket 0
        (e0, e1]     -> bucket 1
        ...
        (en, +inf)   -> bucket n + 1

    Bucket edges must be finite, strictly increasing numbers. The first bucket
    catches every timestamp before or equal to the first edge, and the last
    bucket catches every timestamp strictly after the last edge. This is
    deliberately permissive at the ends so callers never have to deal with a
    "no bucket" value unless they want to; if they need tighter bounds they
    can add sentinel edges themselves.

    The class is frozen because bucket boundaries should not change after
    construction. Rebuilding a bucketer is cheap, and immutability removes a
    whole category of state-management bugs in long-running aggregations.
    """

    edges: Tuple[float, ...]

    def __init__(self, edges: Iterable[Real]) -> None:
        """Create a bucketer from an iterable of bucket right edges.

        Args:
            edges: Finite, strictly increasing bucket edges in seconds.

        Raises:
            ValueError: If the edges are not strictly increasing, contain a
                non-finite value, or are empty. An empty bucket set is
                rejected because the index returned for any timestamp would be
                ambiguous and therefore useless for aggregation.
            TypeError: If an edge cannot be converted to float.
        """
        edge_list = [float(edge) for edge in edges]
        if not edge_list:
            raise ValueError("at least one bucket edge is required")
        if any(not (edge == edge and edge not in (float("inf"), float("-inf"))) for edge in edge_list):
            raise ValueError("bucket edges must be finite")
        for left, right in zip(edge_list, edge_list[1:]):
            if right <= left:
                raise ValueError("bucket edges must be strictly increasing")
        object.__setattr__(self, "edges", tuple(edge_list))

    def bucket_for(self, timestamp: Timestamp) -> int:
        """Return the bucket index for a timestamp.

        Timestamps are seconds since an arbitrary epoch, matching the unit used
        for bucket edges. Integers and floats are both accepted; the input is
        converted to float before comparison. The returned index is the number
        of bucket edges that are strictly less than the timestamp.

        Args:
            timestamp: A finite numeric timestamp.

        Returns:
            An integer bucket index in ``[0, len(edges)]``.

        Raises:
            ValueError: If ``timestamp`` is NaN.
            TypeError: If ``timestamp`` is not numeric.
        """
        value = float(timestamp)
        if value != value:
            raise ValueError("timestamp must not be NaN")
        return bisect_right(self.edges, value)

    def bucket_many(self, timestamps: Iterable[Timestamp]) -> List[int]:
        """Return bucket indices for a sequence of timestamps.

        This is a convenience wrapper around :meth:`bucket_for` that preserves
        the caller's iteration order. It exists because aggregation code almost
        always processes many timestamps together, and keeping the mapping in
        one place makes the bucketer easier to test and easier to swap for a
        vectorised implementation later.
        """
        return [self.bucket_for(ts) for ts in timestamps]


def bucket_timestamps(
    timestamps: Iterable[Timestamp], edges: Sequence[Real]
) -> List[int]:
    """One-shot convenience function: build a bucketer and bucket timestamps.

    Args:
        timestamps: Timestamps to bucket.
        edges: Bucket right edges for :class:`TimeBucketer`.

    Returns:
        Bucket indices in the same order as ``timestamps``.
    """
    return TimeBucketer(edges).bucket_many(timestamps)
