"""
The file you modify. It must define `primes(n)` returning all primes <= n
in increasing order (list or numpy array of ints). Everything else about the
implementation is fair game.
"""

import math
import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np

# Segment size in number of wheel entries. Sized both to stay cache-resident
# and to split n=1e8 into ~4 independent segments. numpy releases the GIL for
# the strided fills and flatnonzero, so the segments run in parallel threads.
SEGMENT = 8_500_000
# Memory bandwidth (not cores) is the limit for the strided writes: past ~4
# concurrent write streams the shared bandwidth saturates and it slows down.
MAX_WORKERS = min(4, os.cpu_count() or 1)


def _small_odd_primes(limit):
    """Odd primes <= limit via a plain odd-only sieve (limit ~ sqrt(n))."""
    size = (limit - 1) // 2 + 1
    s = np.ones(size, dtype=bool)
    s[0] = False  # value 1
    for p in range(3, int(limit**0.5) + 1, 2):
        if s[(p - 1) // 2]:
            s[(p * p - 1) // 2 :: p] = False
    return 2 * np.flatnonzero(s) + 1


def primes(n):
    """Segmented, multithreaded mod-6 wheel sieve of Eratosthenes.

    Only numbers coprime to 6 are represented (density 1/3 vs 1/2 for odd-only),
    interleaved into a single index space so the result comes out already sorted:
        even index j = 2i  -> value 6i+5  (== 5 mod 6)
        odd  index j = 2i+1 -> value 6i+7  (== 1 mod 6)
    so value(j) = 3*j + 5 - (j & 1). Crossing out multiples of a prime p hits
    each residue class with stride 2p. The index space is cut into cache-sized
    segments processed independently, which also makes them trivially parallel.
    """
    if n < 5:
        return np.array([x for x in (2, 3) if x <= n], dtype=np.int64)

    limit = int(n**0.5)
    sp = _small_odd_primes(limit)  # 3 is skipped below; its multiples aren't in the wheel

    # Highest interleaved index j whose value is <= n.
    iB = (n - 5) // 6  # class 6i+5
    iA = (n - 7) // 6  # class 6i+7
    m = max(2 * iB, 2 * iA + 1) + 1

    # Per prime, stride 2p and the first crossout index in each residue class.
    strides, first = [], []
    for p in sp.tolist():
        if p < 5:
            continue
        inv6 = pow(6, -1, p)
        pp = p * p
        i0 = (pp - 5 + 5) // 6  # smallest i with 6i+5 >= p*p ...
        i0 += (((-5 * inv6) % p) - i0) % p  # ... and (6i+5) % p == 0
        i1 = max(0, (pp - 7 + 5) // 6)  # smallest i with 6i+7 >= p*p ...
        i1 += (((-7 * inv6) % p) - i1) % p  # ... and (6i+7) % p == 0
        strides.append(2 * p)
        first.append((2 * i0, 2 * i1 + 1))

    def sieve_segment(jbase):
        cnt = min(SEGMENT, m - jbase)
        buf = np.ones(cnt, dtype=bool)
        for s, (gB, gA) in zip(strides, first):
            for g in (gB, gA):
                if g >= jbase:
                    ls = g - jbase
                else:
                    ls = g + ((jbase - g + s - 1) // s) * s - jbase
                if ls < cnt:
                    buf[ls:cnt:s] = False
        j = np.flatnonzero(buf)
        j += jbase  # global interleaved index
        v = 3 * j
        v += 5
        v -= j & 1  # value = 3j + 5 - (j & 1)
        return v

    bases = range(0, m, SEGMENT)
    if MAX_WORKERS > 1:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            parts = list(ex.map(sieve_segment, bases))
    else:
        parts = [sieve_segment(b) for b in bases]

    return np.concatenate([np.array([2, 3], dtype=np.int64), *parts])
