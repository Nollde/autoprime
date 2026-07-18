"""
The file you modify. It must define `primes(n)` returning all primes <= n
in increasing order (list or numpy array of ints). Everything else about the
implementation is fair game.
"""


def primes(n):
    """Baseline: simple sieve of Eratosthenes on a bytearray."""
    if n < 2:
        return []
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for p in range(2, int(n**0.5) + 1):
        if sieve[p]:
            sieve[p * p :: p] = bytes(len(range(p * p, n + 1, p)))
    return [i for i in range(2, n + 1) if sieve[i]]
