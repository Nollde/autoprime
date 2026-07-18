# primes

An [autoresearch](https://github.com/karpathy/autoresearch)-style experiment: an LLM autonomously researches the fastest possible Python function that generates all prime numbers up to a given `n`.

- `program.md` — the program the LLM follows: setup, experiment loop, logging rules.
- `evaluate.py` — fixed evaluation harness (do not modify): times `primes(n)`, verifies the result is exactly the set of all primes `<= n`, reports `best_seconds` and peak memory.
- `primes.py` — the single file the LLM iterates on. Must define `primes(n)` returning all primes `<= n` in increasing order.
- `results.tsv` — experiment log (untracked), one row per experiment.

Allowed tools: Python standard library + numpy. No sympy, no primesieve, no compiled extensions.

## Run the evaluation

```
uv run evaluate.py              # default n = 10^8
uv run evaluate.py --n 1e7      # smaller n for quick checks
```

Timings are only comparable at the same `n`.
