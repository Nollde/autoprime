"""
The file you modify. It must define `primes(n)` returning all primes <= n
in increasing order (list or numpy array of ints). Everything else about the
implementation is fair game.
"""

import numpy as np

# Segment size in number of wheel entries. Sized so each segment's write
# traffic stays cache-friendly instead of thrashing the full ~n/3 array once
# per small prime. ~12M entries (~12 MB) is empirically the sweet spot at n=1e8.
SEGMENT = 12_000_000


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
    """Segmented mod-6 wheel sieve of Eratosthenes.

    Only numbers coprime to 6 are represented (density 1/3 vs 1/2 for odd-only),
    interleaved into a single array so the result comes out already sorted:
        even index j = 2i  -> value 6i+5  (== 5 mod 6)
        odd  index j = 2i+1 -> value 6i+7  (== 1 mod 6)
    so value(j) = 3*j + 5 - (j & 1). Crossing out multiples of a prime p hits
    each residue class with stride 2p. The range is processed in cache-sized
    segments to keep the working set hot.
    """
    if n < 5:
        return np.array([x for x in (2, 3) if x <= n], dtype=np.int64)

    limit = int(n**0.5)
    sp = _small_odd_primes(limit)  # 3 is harmless (its multiples aren't in the wheel)

    # Highest interleaved index j whose value is <= n.
    iB = (n - 5) // 6  # class 6i+5
    iA = (n - 7) // 6  # class 6i+7
    m = max(2 * iB, 2 * iA + 1) + 1

    # Per prime, precompute stride 2p and the first crossout index in each class.
    strides, first = [], []
    for p in sp.tolist():
        if p < 5:
            continue
        inv6 = pow(6, -1, p)
        pp = p * p
        # class 6i+5 (even j): smallest i with 6i+5 >= p*p and (6i+5) % p == 0
        i0 = (pp - 5 + 5) // 6
        i0 += (((-5 * inv6) % p) - i0) % p
        gB = 2 * i0
        # class 6i+7 (odd j): smallest i with 6i+7 >= p*p and (6i+7) % p == 0
        i1 = max(0, (pp - 7 + 5) // 6)
        i1 += (((-7 * inv6) % p) - i1) % p
        gA = 2 * i1 + 1
        strides.append(2 * p)
        first.append((gB, gA))

    buf = np.empty(SEGMENT, dtype=bool)
    chunks = [np.array([2, 3], dtype=np.int64)]
    for jbase in range(0, m, SEGMENT):
        cnt = min(SEGMENT, m - jbase)
        buf[:cnt] = True
        for s, (gB, gA) in zip(strides, first):
            for g in (gB, gA):
                if g >= jbase:
                    ls = g - jbase
                else:
                    ls = g + ((jbase - g + s - 1) // s) * s - jbase
                if ls < cnt:
                    buf[ls:cnt:s] = False
        j = np.flatnonzero(buf[:cnt]) + jbase
        chunks.append(3 * j + 5 - (j & 1))

    return np.concatenate(chunks)
