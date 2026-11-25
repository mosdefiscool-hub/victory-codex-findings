# Evidence for the opening-scene experiments

Research and evidence extraction by **OpenAI Codex**.

The benchmarks were recorded on November 25–26, 2026 on an NVIDIA GeForce RTX 3080 using the Series X profile. The nested-wave pipeline census used a 32-lane host wave. The driver in the publication-time display inventory was `32.0.16.1088`. The archived run logs do not establish the driver version for each run.

| Release asset | Contents |
| --- | --- |
| `nested-wave-opening.zip` | Present intervals in milliseconds, timing summaries, last reported pipeline queue depth, and anonymous outcomes for 36 programs |
| `bvh-constructor.zip` | Before-and-after header comparison counts and one aggregate pre-dispatch fixture index range |
| `evidence-manifest.json` | Archive and member sizes in bytes, SHA-256 digests, and benchmark metadata |

Each ZIP contains one JSON file. The exports are assembled from allow-listed measurements, categorical outcomes, and run labels. Shader census row numbers are assigned by sorting outcome combinations, so they carry no relationship to original program identifiers, file order, or capture order. Frame timing comes from consecutive present timestamps and is represented as elapsed milliseconds from one present to the next.

## Nested-wave translation and opening timings

The translator census follows the same 36 distinct missing-pipeline reports from one opening capture. An outcome counts as a success when the program both passed SDK validation and created a D3D12 pipeline on the RTX 3080.

| Translator | Validated pipelines | Multi-Wave64 refusals | Whole-wave section refusals | Descriptor refusals |
| --- | ---: | ---: | ---: | ---: |
| Original | 4 | 28 | 1 | 3 |
| Counted loops | 6 | 26 | 1 | 3 |
| Nested loops | 15 | 17 | 1 | 3 |

The runtime runs used the same save and normal scheduling after the desktop session reconnected. The timing window starts at the first world frame and includes up to 40 consecutive present intervals. The 95th percentile uses nearest rank.

| Run | Intervals | Median (ms) | 95th percentile (ms) | Mean (ms) | Last reported pipeline queue |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control `e0672ae` | 2 | 2,099.2 | 2,166.8 | 2,099.2 | 0 |
| Candidate `1bd6050` | 40 | 1,681.8 | 4,835.3 | 1,859.2 | 1,707 |
| Candidate repeat `1bd6050` | 40 | 1,249.7 | 3,466.5 | 1,633.3 | 1,347 |

The control lost the GPU device after two intervals. Both candidate runs reached the 40-interval measurement limit and the opening was still nearly black. The short control and active pipeline queues prevent an estimate of the frame cost of the translation change.

## BVH constructor

The ordered diagnostic captures compared header dwords 3, 13, 14, and 15 immediately before and after each isolated constructor dispatch with stride zero. Source and scratch-counter addresses were used to match records within each run.

| Build | Matched dispatches | At least one selected word changed | All selected words preserved |
| --- | ---: | ---: | ---: |
| `7c11041` | 2,244 | 37 | 2,207 |
| `243a0b8` | 2,763 | 0 | 2,763 |

In one pre-dispatch GPU readback from the older build, the header specified 5,021 primitives and the index buffer contained 5,021 distinct entries. The valid index range was 0–5,020. Six consecutive entries at positions 3,493–3,498 fell outside that range, with a minimum of 1,031,606,225 and a maximum of 1,047,728,174. The buffer was missing six valid indices. The fixture was selected by a later header change, so it supplies an example of the input condition, rather than its frequency. Multiple commits separate the two builds, and the captures compare these four fields under the ordered diagnostic schedule.

## Recompute and verify

With the original local benchmark directory available, regenerate the archives with Python 3.9 or later. The exporter reads private logs and two buffers locally and writes the evidence ZIPs and manifest to `dist/` by default.

```powershell
python tools/export_evidence.py "<local benchmark directory>"
python tools/verify_evidence.py
```

For release downloads, pass the directory that holds the two ZIPs and manifest to the verifier. It checks the published bytes and recomputes timing and census summaries from the released samples. It also checks that the published BVH counts and range bounds are internally consistent.

```powershell
python tools/verify_evidence.py "<download directory>"
```
