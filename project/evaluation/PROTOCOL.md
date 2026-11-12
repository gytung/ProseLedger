# Controlled paired revision study

This protocol is frozen before model inference. Twelve new author-constructed manuscripts cover distinct scientific and applied settings. Each manuscript contains six sections, two controlled source packets and six explicit reference facts. The packets are evaluation fixtures, not published papers or independently collected domain evidence. The manuscripts are not human-authorship samples. This study tests controlled revision behaviour and does not estimate performance on a representative population of scientific papers.

## Comparison

Each input is processed by two conditions:

- **Generic**: section-level copy-editing with a general fluency, clarity and academic-readability instruction and the same preservation requirements.
- **Rules**: the released six-rule section-level instruction, followed by the same released verification, bounded-repair and retention procedure.

Both conditions use Qwen2.5-7B-Instruct Q4_K_M through Ollama for the six section rewrites, with temperature 0.2 and section seeds 42–47. The canonical model digest is recorded. The same hosted reviewer, gpt-6.1-sol through the official signed-in CLI, handles section review, bounded repair and final audit. The same source packet, original manuscript, length bounds, citation checks, repair policy and final retention rule are used. The generic condition omits the six-rule list and detailed naturalization instruction; the remaining preservation constraints are retained. No historical memory cards are retrieved in either condition.

Each condition has six writer calls. Review and repair calls may differ because they depend on findings; actual calls, tokens and elapsed time are reported. This is a matched writer configuration, not an equal-total-token comparison. Conditions alternate execution order by case. Local writer calls are serialized; one completed case's hosted review may overlap the next case's local writing. Each complete response and rejected candidate is retained. Failed requests are reported and may be resumed using the same inputs and cached completed stages; responses are not resampled to obtain better scores.

## Prespecified measurements

1. Operational completion out of all 24 scheduled runs; candidate retention and changed sections.
2. Preservation of 72 reference facts, assessed against the exact frozen packet and original. Automated entailment judgments are labelled automated and include quoted support. They are not treated as verified human judgments.
3. Branch-blinded pairwise naturalness judgment. The evaluator sees the original and two anonymous retained outputs; the pair is also presented in reversed order. Report both decisions and disagreement. A consistent preference counts as a win or loss; disagreement or an explicit tie counts as inconclusive/tied. This is an LLM proxy, not a human evaluation.
4. GPTZero document probability on original and retained outputs, collected only after all generation and retention decisions have completed. Text hashes link scans to outputs. Identical text is scanned once and shared by hash. Detector output is not used for admission, parameter changes, early stopping or choosing examples. Report every case, mean paired differences and wins/ties/losses using a 0.01 percentage-point tolerance. A lower probability is not evidence that a text is human-authored or scientifically correct.
5. An additional known-answer mutation challenge tests the deterministic preservation guard. Each original has one acceptable meaning-preserving edit and one deliberately invalid edit with an explicit reference explanation. These constructed violations test checker coverage rather than model writing quality.

The 12 manuscripts, scripts and engine files are hashed in freeze.json. No case is removed because its result is unfavourable. The entire case set and all incomplete runs remain in the denominator. Report bootstrap intervals over paired cases for continuous differences and Wilson intervals for proportions. With 12 controlled cases, uncertainty is substantial; no broad superiority claim follows from a positive mean alone.

## Scope relative to earlier results

The earlier four-case Qwen experiment used MLX and a different quantization/runtime. It is a pilot cohort and remains separate. The present Ollama experiment is a new controlled paired test, not a continuation that can be pooled with that cohort. Archived six-case memory/controller results use a different pipeline and rubric and are also reported separately. Existing participant interviews remain qualitative unless their prompts, labels, per-person responses and denominators are verified.
