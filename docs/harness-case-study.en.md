# DraftCut: inspectable edits and two human approvals

[中文](harness-case-study.md) · [Setup](getting-started.md)

The workflow is **spoken-manuscript approval → video-script approval → production**. The Agent proposes semantic edits and reviews the full recording; deterministic code checks source integrity, word accounting, media timing and signed decisions.

[spoken_edit.py](../scripts/spoken_edit.py) reuses clean-talking's conservative candidates and pure timeline helpers. Every word has one keep/delete decision and a reason. Negation, numbers and names have conservative protection; sensitive changes require explicit justification. Reordering is disclosed. Every retained word maps once to an intact source sample interval, and no deleted word may remain in kept audio. Audio is spliced from 48 kHz source PCM and compared byte-for-byte; SRT comes from the same sample map. ASR corrections are disclosed, never synthesized as new speech.

A source video follows the same cuts. Cumulative frame allocation bounds rounding rather than accumulating an independent error at every splice. Complete media decoding and timing checks are required. Incorrect ASR boundaries can still harm perceived speech, so actual listening remains necessary.

[spoken_workflow.py](../scripts/spoken_workflow.py) creates a review-only proxy, source/refined text, word decisions, reasons, corrections and the complete mapped subtitles. Semantic review evidence is bound to the current draft and proxy. Only a valid human manuscript receipt unlocks the formal refined master. The second review binds that master, subtitles, visual script, machine plan and assets. Observed input changes burn the previous generation; reverting an observed changed draft does not resurrect its receipt. Builds use preserved transactions and safe same-version retries.

[Conversational approval](approvals.md) requires the Agent to show the complete current manuscript or director plan and receive an explicit user reply. The Agent then records that reply against the current review digest; users do not configure keys, enter passphrases, or run approval commands. Old booleans, fixture decisions, wrong stages, and stale revisions cannot authorize the current production request.

The pure `validate_plan` function checks structure only. Its production CLI, initialization, rendering and delivery all verify the current two-stage revision-bound approval records. Initialization copies the approved WAV unchanged and creates a scaffold; actual visual production and continuous preview remain separate work. Exported AAC is decoded and compared against the approved voice waveform, including explicit mono/stereo handling. Codec tolerance is not semantic listening certification.

Run the commands in the [local verification guide](getting-started.md#local-verification). Fixtures use known tones and authored timestamps, no private recordings, live ASR, paid API or genuine human approvals. Coverage includes semantic edit selections, intentional repetition, protected terms, reorder/sample/SRT integrity, A/V cuts, both gates, stale/forged approvals and explicit legacy migration. Real speech accuracy, naturalness and visual quality still require authorized media and actual review. The efficiency ambition is not benchmarked.

## Repository-link setup verification

An independent execution Agent read the public repository entry, then the bootstrap guide and Skill, and installed a fresh project virtual environment and locked Node packages on this macOS Apple Silicon host. A second check reused those packages. Both runs executed full local Chrome with GSAP and an H.264/AAC encode/full-decode check. Using the reported runtime, it initialized the synthetic composition and linted it with zero errors or warnings.

Existing system Python, Node, FFmpeg and Chrome were reused. This validates the isolated project setup path on this host, not a fresh OS installation, every Agent, cloud ASR or production approvals. The [Agent setup guide](agent-bootstrap.md) owns the technical steps; the user only sends the repository link.
