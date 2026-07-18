"""
The file you modify. It must define `primes(n)` returning all primes <= n
in increasing order (list or numpy array of ints). Everything else about the
implementation is fair game.
"""

import numpy as np

# Segment size in number of odd entries. Chosen so each segment's write
# traffic stays cache-friendly relative to streaming the full n/2 array once
# per small prime. ~8M odds (~16 MB) is empirically the sweet spot at n=1e8.
SEGMENT_ODDS = 8_000_000


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
    """Segmented odd-only sieve of Eratosthenes.

    The [0, n] range of odd numbers is processed in cache-sized segments. Each
    segment is crossed out by every prime <= sqrt(n), which keeps the working
    set hot in cache instead of thrashing the full n/2 array once per prime.
    """
    if n < 2:
        return np.array([], dtype=np.int64)
    if n == 2:
        return np.array([2], dtype=np.int64)

    limit = int(n**0.5)
    sp = _small_odd_primes(limit)  # odd primes <= sqrt(n)
    total_odds = (n - 1) // 2 + 1  # index i -> value 2*i+1

    seg = SEGMENT_ODDS
    buf = np.empty(seg, dtype=bool)
    out_chunks = [np.array([2], dtype=np.int64)]

    for base in range(0, total_odds, seg):
        cnt = min(seg, total_odds - base)
        buf[:cnt] = True
        lo = 2 * base + 1  # first odd value in this segment
        hi = lo + 2 * (cnt - 1)  # last odd value in this segment
        for p in sp:
            pp = p * p
            if pp > hi:
                break  # remaining primes only matter in later segments
            if pp >= lo:
                m = pp
            else:
                # smallest multiple of p that is >= lo, forced odd (p is odd)
                m = ((lo + p - 1) // p) * p
                if m % 2 == 0:
                    m += p
            buf[(m - lo) // 2 : cnt : p] = False
        if base == 0:
            buf[0] = False  # value 1 is not prime
        out_chunks.append(2 * (base + np.flatnonzero(buf[:cnt])) + 1)

    return np.concatenate(out_chunks)
