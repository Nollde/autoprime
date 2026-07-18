"""
Fixed evaluation harness. Do not modify this file.

Imports `primes` from primes.py, times it, and verifies the result is exactly
the set of all primes <= n (nothing missing, nothing composite, sorted, unique).

Usage:
    uv run evaluate.py              # default n
    uv run evaluate.py --n 1e7      # override n (int or scientific notation)

On success it prints a summary block; the key metric is `best_seconds`.
On verification failure it prints details and exits non-zero WITHOUT printing
the summary block, so `grep "^best_seconds:" run.log` comes up empty.
"""

import argparse
import resource
import sys
import time

import numpy as np

from primes import primes

DEFAULT_N = 100_000_000
NUM_RUNS = 3

# pi(n) for common n, used to sanity-check the reference sieve itself.
KNOWN_PRIME_COUNTS = {
    10**5: 9_592,
    10**6: 78_498,
    10**7: 664_579,
    10**8: 5_761_455,
    10**9: 50_847_534,
}


def reference_primes(n: int) -> np.ndarray:
    """Trusted reference: plain numpy sieve of Eratosthenes."""
    if n < 2:
        return np.array([], dtype=np.int64)
    sieve = np.ones(n + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(n**0.5) + 1):
        if sieve[p]:
            sieve[p * p :: p] = False
    return np.flatnonzero(sieve).astype(np.int64)


def verify(result, n: int) -> None:
    """Exit with an error message if `result` is not exactly all primes <= n."""
    try:
        arr = np.asarray(result, dtype=np.int64).ravel()
    except (TypeError, ValueError) as e:
        sys.exit(f"VERIFICATION FAILED: result could not be converted to an integer array: {e}")

    ref = reference_primes(n)
    if n in KNOWN_PRIME_COUNTS:
        assert len(ref) == KNOWN_PRIME_COUNTS[n], "internal error: reference sieve is wrong"

    if np.array_equal(arr, ref):
        return

    ref_set = set(ref.tolist())
    got_set = set(arr.tolist())
    missing = sorted(ref_set - got_set)
    extra = sorted(got_set - ref_set)
    msgs = ["VERIFICATION FAILED:"]
    msgs.append(f"  expected {len(ref)} primes, got {len(arr)} values ({len(got_set)} unique)")
    if missing:
        msgs.append(f"  missing {len(missing)} primes, first few: {missing[:10]}")
    if extra:
        msgs.append(f"  {len(extra)} values that are not primes <= n, first few: {extra[:10]}")
    if not missing and not extra:
        msgs.append("  correct set of values, but not sorted and/or contains duplicates")
    sys.exit("\n".join(msgs))


def peak_mem_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, kilobytes on Linux
    return rss / (1024 * 1024) if sys.platform == "darwin" else rss / 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=str, default=str(DEFAULT_N),
                        help="generate all primes <= n (int or scientific, e.g. 1e8)")
    args = parser.parse_args()
    n = int(float(args.n))

    times = []
    result = None
    for i in range(NUM_RUNS):
        t0 = time.perf_counter()
        out = primes(n)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if i == 0:
            result = out
        print(f"run {i + 1}/{NUM_RUNS}: {t1 - t0:.6f}s", flush=True)

    verify(result, n)
    num_primes = len(reference_primes(n)) if n not in KNOWN_PRIME_COUNTS else KNOWN_PRIME_COUNTS[n]

    print("---")
    print(f"n:            {n}")
    print(f"best_seconds: {min(times):.6f}")
    print(f"mean_seconds: {sum(times) / len(times):.6f}")
    print(f"runs_seconds: {', '.join(f'{t:.6f}' for t in times)}")
    print(f"num_primes:   {num_primes}")
    print(f"correct:      True")
    print(f"peak_mem_mb:  {peak_mem_mb():.1f}")


if __name__ == "__main__":
    main()
