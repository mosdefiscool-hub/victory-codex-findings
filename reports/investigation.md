# VIctory on an RTX 3080

Opening-scene investigation, November 25–26, 2026. Research and engineering by OpenAI Codex.

## Current result and priorities

The local VIctory build can reach the GTA VI opening on an RTX 3080 with a Series X profile. An early build reached the movement tutorial at roughly 1–2 FPS with heavy overexposure. Later connected-session runs recovered additional shader pipelines and completed the measured opening window, but the captured scene was nearly black and the pipeline queue still had more than a thousand builds pending. The captures establish world entry and several specific correctness fixes. Their timing is insufficient to attribute a frame-rate change to an individual patch.

1. Reproduce the dark opening on the current build with normal scheduling and a warmed pipeline cache. Compare matched scene poses and record the pending-build count, missing-pipeline hashes, exposure output and the values consumed by subsequent passes. Recovering the exposure dispatch and observing changing output are already established.
2. Re-census named drops after the build queue drains. Prioritize high-frequency programs that feed missing rendering work. Conditional shared-LDS Wave64 groups remain the largest refusal class in the isolated opening sample.
3. Repeat the command-cost capture using the corrected timestamp boundaries. Use separate, uninstrumented present measurements for pacing. Verify the isolated BVH copy and its producer inputs if device removal recurs on the current build. The strongest evidence for a malformed copy count comes from the older build.
4. Reproduce the startup serializer assertion under matched Windows session conditions if it recurs. The disconnected-session audio failure was measured with a standalone probe. The title's audio calls and their relationship to the repeated serializer batch remain unverified.

## Opening benchmarks

The tests used an RTX 3080, a Series X profile and a shared save seed within each comparison. Unless stated otherwise, each row reports the first 40 consecutive world-present intervals for one run. The workload evolves through the cutscene. Pipeline readiness, dispatch tracing and queue scheduling affect comparisons. Rows from separate experiments may use different controls.

| Comparison | Revision and run | Median (ms) | p95 (ms) | Mean (ms) |
| --- | --- | ---: | ---: | ---: |
| Ordered half sums and heap sync | Copy refresh, `3a3c8f5` | 866.6 | 3433.7 | 1334.1 |
| | Half sums, `e48ef49` | 1112.6 | 3166.7 | 1466.7 |
| | Deferred heap views, `14057ff` | 666.4 | 2000.3 | 879.7 |
| First-use texture placement | Matched deferred-view control, `14057ff` | 698.6 | 2166.5 | 895.8 |
| | First-use allocation, `50ee2c1` | 599.5 | 2033.0 | 894.1 |
| Cooperative histogram | First-use allocation, `50ee2c1` | 599.5 | 2033.0 | 894.1 |
| | Cooperative Wave64, `a8ad6c3` | 783.4 | 1966.2 | 1108.3 |
| Texture readback | Matched cooperative control, `a8ad6c3` | 783.2 | 1999.8 | 961.3 |
| | Texture readback, `1840202` | 716.8 | 1899.8 | 949.9 |
| Material depth | Matched readback control, `1840202` | 848.0 | 2666.4 | 1168.2 |
| | Float material depth, `02d62d2` | 1006.6 | 2765.2 | 1252.5 |
| Exposure | Lane-proof control | 703.7 | 3900.2 | 1234.2 |
| | Exposure lowering, `e851169` | 482.5 | 1657.5 | 692.0 |
| Root constants | Binding-diagnostic control | 683.6 | 2900.5 | — |
| Hierarchy producer | Device fence, `e0672ae`, isolated | 1933.4 | 4965.4 | — |
| | Device fence, ordered segments | 1200.4 | 2766.8 | 1433.3 |
| | Device fence, normal scheduling | 966.4 | 2900.2 | 1260.9 |
| Nested loops | `1bd6050`, connected, normal scheduling | 1681.8 | 4835.3 | — |
| | `1bd6050`, connected repeat | 1249.7 | 3466.5 | — |

The readback comparison overlapped part of another workload, and the exposure control overlapped the shader suite while part of the candidate overlapped builds. Its repeat control exited before world entry with a guest null write. The final reports for the nested-loop runs showed 1,707 and 1,347 pending pipeline builds. In that connected session the unchanged `e0672ae` reached the world and lost the device after two measured intervals.

An earlier rectangle-versus-copy-refresh comparison used the first 11 diagnostic reporting intervals averaging at least 500 draws per frame, with zero pipeline construction at the median. Median reported frame / preparation / copy / GPU times were 2,029.7 / 644.3 / 207.3 / 1,419.0 ms on `099f538`, and 2,867.1 / 467.6 / 217.3 / 1,491.5 ms on `3a3c8f5`. Median copy volumes were 242.7 and 265.7 MB. Median draws per frame were 1,716 and 1,795. Those reporting intervals differ from the consecutive-present measurements in the table.

## Rendering and shader translation

| Revision | Change and verification | Remaining question |
| --- | --- | --- |
| `099f538` | Corrected lighting rectangle completion. A CPU vertex check and hardware tile-boundary regression failed before the fix and passed after it. The title created rectangle pipelines. | Severe lighting errors persisted. |
| `e48ef49` | Replayed ordered half-precision sums for `b22a16a178976e1b` on a 32-lane target. RTX readback checked four logical waves, partial masks, both halves, per-add rounding and the preserved upper word. The original container validated, created a pipeline and reached the 500-command live trace limit. | Full-pass pixel output lacks a reference. The preceding build dropped a median 28 dispatches per frame for this hash across 12 zero-pending reporting intervals. |
| `a8ad6c3` | Preserved shared LDS and synchronization for the 512-thread Wave64 BVH histogram `14394a322f6dd5c2`. Four RTX readbacks matched all 2,560 bins over 20,480 keys against a CPU histogram. The trace recorded 228 live dispatch commands. | Overexposure persisted. Divergent barriers in 128-thread shaders `9f017d9011377efa` and `87bf9e3f2bf2f052` remained unsupported. |
| `1840202` | Implemented texture-to-buffer readback. The GPU round-trip regression passed, and the opening recorded 5×1 and 1×1 copies of 80 and 16 bytes. | The scene still lacked detail and clipped highlights. The producing pass and the downstream consumer require live value comparisons. |
| `02d62d2` | Preserved integer material IDs in 32-bit float depth for exact rasterizer EQUAL tests. The GPU matched 4,096/4,096 IDs after conversion versus 3,875/4,096 with 24-bit depth. The test covered reverse conversion and stencil. | Extensive lighting loss persisted. |
| `e851169` | Proved group-uniform or thread-zero first-lane reads and safe LDS phases. The 1×1 exposure producer `e622b718b6d9b057` matched all eight buffer and texture output components on 33 inputs against a guest-instruction CPU model, including the live texture dimensions and histogram formats. A trace recorded 44 live producer dispatches and changing nonzero output. | Downstream consumption remains unverified. The second recovered program, `647d1f745d5a8a3a`, has SDK and pipeline validation only. |
| `cc28e6e` | Proved lane zero keeps the guest mask nonempty at eight guards in radix program `e63d22c4def9ba6a`, preserving 17 workgroup barriers. Seven full-backing GPU readbacks matched a CPU stable radix pass, including keys, payloads and guard space. | Scene effect and timing remain unmeasured. |
| `f86b9cb` | Lowered direct pixel barycentrics. An unequal-clip-W triangle verified perspective and linear values at 256 pixel centers. Three original pixel shaders created standalone pipelines. The reported opening pixel shader `98bd9f9ae5f9c7e3` also linked with vertex shader `2fa687db9a9f04fd` under the adapter's test pipeline settings. | The captured pixel hash accounted for 3.0 drops per frame in five reporting periods. Recovered live draws remain unmeasured. |
| `554ba12` | Preserved the scalar condition implied by an EXEC branch. A 32-output loop-exit regression matched on RTX and WARP. The original programs `82a2ad6d07417d36` and `90a0692af4320129` validated and created pipelines. | Live dispatch and scene output remain unmeasured. |
| `dba92a1`, `1bd6050` | Proved counted-loop progress and convergence of nested bit scans before partitioning independent guest waves. Synthetic RTX regressions matched all 256 dwords in each case. A memory-polling loop and invalid progress cases remained refused. | Title-program results here establish pipeline creation. Matched readbacks, recovered dispatch counts and post-build-queue scene impact remain open. |

In one opening capture, 36 distinct missing-pipeline hashes were matched to their containers. The controlled fixed-32-lane pipeline retest moved from 4/36 at `314ad78`, to 6/36 after counted loops, to 15/36 after nested loops. Of the remaining 21, 17 were multi-Wave64 groups, one involved a whole-wave section, and three involved descriptors. The separate historical 98-program large-Wave64 sample went from 14 emissions before cooperative histogram work to 15 after, and 17 after exposure lowering. The broader census used a 26,136-program baseline at `7e37f28`. Each population answers a different question.

The separate BVH library reached 49 validated pipelines out of 52 after radix support. Three remained unsupported at library offsets `0x99160`, `0x9a830` and `0x9be80`. Each has a backward conditional branch. The frequently dropped meshlet culling shaders and their shadow variant also need conditional control flow around wave operations and workgroup barriers. A refused mixed-format mesh pipeline was observed earlier in the opening.

## Memory, descriptors and CPU preparation

- **Dynamic reserve.** Increasing the dynamic reserve from 65,536 to 262,144 in the capped one-million-slot heap reached the movement tutorial with zero dynamic-slot exhaustion warnings in the observed run. The preceding build stopped at the guest `INSTANCE_LIST` limit with 45,000/45,000 entries.
- **Unchanged reads and deferred views.** `3a3c8f5` passed the formerly failing unchanged-buffer batch regression including GPU readback after a page write. `14057ff` avoided rebuilding deferred placed-texture slots at each heap sync. Its hardware test verified the deferred view survives repeated syncs and the first draw creates the host texture. The unrelated heap-capacity assertion failed on the parent and candidate.
- **First-use host textures.** `50ee2c1` combined compatible access flags for aliases and deferred host allocation until use. The matched control and candidate saw allocated host textures fall from 9,062.5 to 4,994.5 MB and snapshots from 703.1 to 364.1 MB/frame, as medians of six diagnostic samples. Mean present interval was 895.8 versus 894.1 ms.
- **Root constants.** Diagnostics in `a201715` and `32c578e` identified 11 shaders affected by mixing up constants and root buffer descriptors. Seven zero-pending samples had a median 590 of 636 direct-command drops per frame attributed to this cause. `d2b3e47` bound the fifth constant dword as data and preserved descriptor offsets. Graphics and compute regressions passed. Both candidate launches lost the device before world entry, which shifted the investigation to the restored hierarchy dispatches.
- **Root UAV boundaries.** `f5d457b` saved both boundary pages of a root UAV range, limited by buffer bounds, and reconciled marked writes bytewise. The GPU regression recovered both previously lost edge writes and preserved the root and independent title writes.
- **Adapter-sized descriptor heaps.** `431107e` used the bound heap layout for translation, cache and allocation. NVIDIA selected one million slots, below the old emitter limit of 2,097,152. RTX and WARP tests verified valid buffer data, a texture substituted for a buffer, and out-of-heap access routed to a physically present null slot. World entry was blocked by the serializer assertion during the disconnected-session control.
- **Dynamic descriptor metadata.** `20fb843` retained four metadata words for a dynamic slot until first shader use publishes the address table. A regression verified replacement and clearing as well as subsequent updates. Opening impact was unmeasured.
- **Snapshot extension.** One diagnostic period reported 1,147.4 MB of snapshot copying per frame for a single 64 MiB backing. `f8eea0c` appended only uncovered bytes during forward growth and preserved the original data of bridged snapshots. A 16 MiB synthetic adjacent-range benchmark reduced median CPU declaration time from 34.171 to 1.370 ms after excluding the first of six runs. The affected pattern's frequency and savings in the live opening remain unmeasured.

## Hierarchy dispatches and profiling

An isolated 709-workgroup ConstructBVH4 dispatch, `5552dac6a2b7a1fd`, was unfinished in DRED after the root-constant fix. The original program waited for globally coherent node data before publishing an atomic counter. The translator dropped both GFX10 waits and read through a separate read-only view. `e0672ae` added the drained wait and device fence handling and coherent UAV reads. A 16-workgroup publication test checked counters and payloads, and the same isolated dispatch passed in a run that completed 40 world intervals. `f6ada00` extended the fence handling to intervening scalar operations and allocated LDS. An earlier standalone LDS read-barrier experiment emitted byte-identical DXIL for all 47 programs it translated and was set aside.

The partial timing run at `7c11041` reached 29 measured world intervals before device removal. Sampled totals included 2,327.3 ms for 17 LoadPrimitivesConstants dispatches (`5062bc7a48e842f8`), 1,277.1 ms for 61 fill dispatches (`3b90165a77d95cdf`), and 1,002.8 ms for 17 Box32 dispatches. An earlier capture sampled 1,862.7 ms across 28 Box32 dispatches (`28918b7150a7aad5`), with a maximum of 184.9 ms. The profiler serializes command lists and only reports the six longest intervals from lists over 50 ms. `2583725` fixed the boundary of the final measured command in a saturated query heap. `ca2059f` placed the end of a direct dispatch before the next binding so later preparation gets a separate marker.

The isolated fill-placement fixture used direct-queue timestamps and checked all output words and guards in 132 readbacks. Median GPU times for default versus system memory (custom WRITE_BACK, L0) were 6.144 versus 6.144 µs for 21 groups, 12.080 versus 18.432 µs for 400 groups, and 27.088 versus 902.064 µs for 1,256 groups. Isolated system-memory time peaked at 2.112 ms. The old live list sometimes attributed over 30 ms to the fill interval and could include preparation for the following command. The standalone comparison establishes a placement cost at the largest tested size. Its contribution to live frame time is unmeasured.

## Malformed BVH input on the older build

The incomplete timing run stopped within a sequence of 128-group BVH copies (`c42a31951201f9a0`). The shader copies 64 × (node count + 1) bytes and can reset bounds. Seven standalone cases matched a CPU reference across an entire 1 MiB backing, including equal and distinct addresses, a multi-iteration 128-group dispatch and bounds reset.

Ordered instrumentation isolated the failing copy on an older diagnostic build based on `7c11041`. The GPU reached command 2 of 3, a single 128-group dispatch. Before it ran, source header word 1 already held 32,553,473, which implied a 2,083,422,336-byte copy. The 422 sampled dispatches all supplied the same address for source and destination and requested no bounds reset. A repeat with an independently allocated source already had 32,562,367 in prepared GPU backing before execution, unchanged after fencing the earlier lists. CPU header reads returned zero for both failing and successful copies, while the GPU backing was populated. The probe left the title's copy length and dispatch behavior intact.

An ordered before/after capture matched ConstructBVH4 records by source and scratch-counter addresses with stride zero. On `7c11041`, 37 of 2,244 matched dispatches changed one or more of header dwords 3, 13, 14 and 15. On `243a0b8`, 0 of 2,763 changed those fields. One old-build readback also caught invalid input **before** construction. A 5,021-primitive case contained six consecutive out-of-range `u7` indices at positions 3,493 through 3,498, replacing six expected indices in the otherwise distinct entries. Multiple patches separate the builds. The comparison leaves the corrupting producer and the change responsible for the newer observation unresolved.

## Startup control

With the Windows desktop disconnected, multiple candidate binaries and the older control hit the same title breakpoint before world entry. The serializer had 98,224 bytes used in a 98,304-byte buffer and attempted to append 1,728 bytes. Forty-two adjacent records shared the new record's first 32 bytes, and 41 matched in full, totaling 72,576 bytes. A fresh pipeline cache and extra free disk space did not resolve the breakpoint.

A standalone XAudio2 probe in the disconnected session returned `0x80070490` when opening default and explicit mastering voices. Title-side audio tracing yielded no events. With the desktop connected, the default endpoints could open shared streams and the default mastering voice opened. The older control and the nested-loop candidate then reached the world. The repeated serializer batch and the endpoint behavior remain separate observations until the title's producer and consumer are traced.

## Evidence scope

Shader identifiers and revision abbreviations identify the local investigation's evidence. SDK validation checks the emitted shader, and driver pipeline creation checks the tested linkage and configuration. A GPU readback compares a defined output under fixture inputs. Live dispatch tracing records commands, and scene captures record what was rendered at a point in the cutscene. Each result above names the level that was actually observed.
