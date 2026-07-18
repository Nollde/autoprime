"""
The file you modify. It must define `primes(n)` returning all primes <= n
in increasing order (list or numpy array of ints). Everything else about the
implementation is fair game.
"""

import numpy as np


def primes(n):
    """Odd-only numpy sieve of Eratosthenes.

    Only odd numbers are stored: index i represents the value 2*i+1.
    Crossing out multiples of p starts at p*p and steps by 2*p (skip evens).
    """
    if n < 2:
        return np.array([], dtype=np.int64)
    if n == 2:
        return np.array([2], dtype=np.int64)

    # sieve[i] represents the odd number 2*i+1, for i in [0, (n-1)//2].
    size = (n - 1) // 2 + 1
    sieve = np.ones(size, dtype=bool)
    sieve[0] = False  # value 1 is not prime

    limit = int(n**0.5)
    for p in range(3, limit + 1, 2):
        if sieve[(p - 1) // 2]:
            # first multiple to cross is p*p; index of value v is (v-1)//2.
            start = (p * p - 1) // 2
            sieve[start::p] = False

    # recover values: odd primes are 2*i+1 for set bits, plus the prime 2.
    odd_primes = 2 * np.flatnonzero(sieve) + 1
    out = np.empty(odd_primes.size + 1, dtype=np.int64)
    out[0] = 2
    out[1:] = odd_primes
    return out
