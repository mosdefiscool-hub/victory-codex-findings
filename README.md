# VIctory on the RTX 3080

**Investigation, experiments and report by OpenAI Codex**, working in a user-directed VIctory checkout. Measurements were collected on one local RTX 3080. VIctory and its contributors provided the compatibility layer. This is an independent research report.

## Start with the nine compute pipelines

The translator refused to split a logical 64-lane wave across 32-lane hardware when it could not prove every loop would terminate independently. Nine shaders in one opening-scene capture used the same nested pattern. The inner counter advances to a fixed bound. The outer loop removes one set bit per iteration. Recognizing both patterns allowed the translator to accept these shaders while retaining the refusal for loops whose progress still depends on other waves.

| Question | Measured result |
| --- | --- |
| What changed for real shader pipelines? | 6 of 36 previously dropped shaders built with the preceding counted-loop implementation. With nested-loop recognition, 15 of the same 36 passed SDK validation and created a pipeline on the RTX 3080. |
| Is the translated output correct? | The synthetic nested-loop shader produced all 256 expected 32-bit words. The nine title shaders have pipeline-creation evidence only. |
| Did the opening scene become playable? | The opening remained nearly black. The first 40 world intervals had median / p95 of 1,682 / 4,835 ms on one run and 1,250 / 3,467 ms on a repeat. Both runs still had queued pipelines. |
| Where did the older GPU hang originate? | A BVH copy received a malformed header. On the older build, four normally preserved fields changed in 37 of 2,244 sampled constructor dispatches. On the newer build they held in all 2,763 samples. Multiple commits separate the builds. |

## Use the findings

- **Reproduce the shader result.** The shader report describes the fix and synthetic test, including the cases that must still be refused. [Shader report](reports/shader.md) · [Reproducer](repro/)
- **Inspect the measurements.** The evidence guide explains the samples, extraction and archive contents. [Evidence guide](reports/evidence.md) · [Tagged releases](https://github.com/mosdefiscool-hub/victory-codex-findings/releases)
- **Trace the wider investigation.** The catalog covers exposure and material depth, wave operations, resource binding, snapshot costs, BVH construction, startup and remaining blockers. [Investigation catalog](reports/investigation.md)

The 36-shader set consists of distinct missing pipelines observed after world entry in one trace. The wider census contained 26,136 programs. The 21 remaining failures in the opening set do not estimate a whole-game failure rate.

For follow-up, capture the first intermediate lighting or material target that diverges in the current dark opening. For performance, repeat the same scene and settings after the pipeline queue drains, with GPU tracing off. Those tests answer different questions from the synthetic correctness check.
