# autoresearch: primes

This is an experiment to have the LLM do its own research. The research problem: write the fastest possible Python function that generates all prime numbers up to a given `n`.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `evaluate.py` — fixed evaluation harness: timing, correctness verification, default `n`. Do not modify.
   - `primes.py` — the file you modify. It must define `primes(n)` returning all primes `<= n` in increasing order.
4. **Agree on `n`**: The default is `n = 10^8`. The user can pick a different value (`uv run evaluate.py --n 1e7`), but it must stay fixed for the whole run — timings at different `n` are not comparable.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment is one invocation of the evaluation harness: `uv run evaluate.py > run.log 2>&1`. It calls `primes(n)` three times, verifies the output is exactly the set of all primes `<= n` (nothing missing, nothing composite, sorted, no duplicates), and reports the best wall-clock time.

**What you CAN do:**
- Modify `primes.py` — this is the only file you edit. Everything is fair game: sieve variants (Eratosthenes, Atkin), wheel factorization, segmentation for cache locality, bytearray/numpy vectorization tricks, precomputation, whatever you can think of.

**What you CANNOT do:**
- Modify `evaluate.py`. It is read-only. It contains the fixed timing methodology, the correctness verification, and the default `n`.
- Install new packages or add dependencies. You can only use what's already in `pyproject.toml`: the Python standard library and numpy. In particular no sympy, no primesieve bindings, no compiled extensions.
- Change `n` between experiments. All results in one run are at the same `n`.

**The goal is simple: get the lowest best_seconds.** The only hard constraint is correctness — the harness verifies the output exactly, and an incorrect result counts as a crash.

**Memory** is a soft constraint. Some increase is acceptable for meaningful speed gains, but it should not blow up dramatically (`peak_mem_mb` is reported by the harness).

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the improvement magnitude. A 1% speedup that adds 40 lines of hacky code? Probably not worth it. A 1% speedup from deleting code? Definitely keep. An improvement of ~0 but much simpler code? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the evaluation harness on `primes.py` as is.

## Output format

Once the harness finishes it prints a summary like this:

```
---
n:            100000000
best_seconds: 12.345678
mean_seconds: 12.501234
runs_seconds: 12.812345, 12.345678, 12.345679
num_primes:   5761455
correct:      True
peak_mem_mb:  812.4
```

You can extract the key metric from the log file:

```
grep "^best_seconds:" run.log
```

If the output is wrong (missing primes, composites included, wrong order, duplicates), the harness prints `VERIFICATION FAILED` with details, exits non-zero, and does NOT print the summary block — so the grep above comes up empty, same as a crash.

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 5 columns:

```
commit	best_seconds	peak_mem_mb	status	description
```

1. git commit hash (short, 7 chars)
2. best_seconds achieved (e.g. 12.345678) — use 0.000000 for crashes and verification failures
3. peak memory in MB, round to .1f — use 0.0 for crashes
4. status: `keep`, `discard`, or `crash`
5. short text description of what this experiment tried

Example:

```
commit	best_seconds	peak_mem_mb	status	description
a1b2c3d	12.345678	812.4	keep	baseline: bytearray sieve of Eratosthenes
b2c3d4e	1.204500	1450.2	keep	numpy sieve with flatnonzero extraction
c3d4e5f	1.310000	980.0	discard	odd-only sieve, index math overhead ate the gains
d4e5f6g	0.000000	0.0	crash	segmented sieve missed primes near segment boundaries
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoresearch/mar5`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `primes.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `uv run evaluate.py > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^best_seconds:\|^peak_mem_mb:" run.log`
6. If the grep output is empty, the run crashed or failed verification. Run `tail -n 50 run.log` to read the error and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
8. If best_seconds improved (lower), you "advance" the branch, keeping the git commit
9. If best_seconds is equal or worse, you git reset back to where you started

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Noise**: Wall-clock timings jitter. The harness already takes the best of 3 runs, but for improvements in the ~1-2% range, re-run once before deciding keep vs discard.

**Timeout**: An experiment should take on the order of a minute (3 timed runs + verification). If a run exceeds 10 minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (exception, verification failure, etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, an off-by-one at a segment boundary), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read up on sieve algorithms, re-read the in-scope files for new angles, try combining previous near-misses, try more radical algorithmic changes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~2 minutes then you can run approx 30/hour, for a total of a few hundred over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!
