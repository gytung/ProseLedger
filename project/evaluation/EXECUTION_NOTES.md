# Execution notes

The two worker threads submit conditions in alternating order by case, as specified in the frozen runner. The local writer lock serializes all six section calls for a condition, but operating-system thread scheduling can invert which condition first acquires the lock. Actual request and response records, rather than the intended submission order, define the execution sequence. There is no shared conversational state between conditions; each section request contains its own frozen input and fixed seed.

Reported wall-clock run durations include time waiting for the shared local writer. `activeModelSeconds` instead sums Ollama's recorded inference durations and hosted response durations. It is the more appropriate measure when comparing computational work under this overlapping execution schedule.

The post-processing scripts `scan_outputs.py` and `summarize.py` do not change generation, admission or the frozen input set. They implement the detector and statistical analyses prespecified in `PROTOCOL.md`. Their hashes are recorded separately in `analysis_freeze.json`.
