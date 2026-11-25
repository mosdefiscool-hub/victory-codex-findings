# Wave64 shader coverage on Wave32 hardware

The nested-loop proof raised successful SDK validation and D3D12 pipeline creation from 6 to 15 of 36 shaders named as missing pipelines in one opening-scene capture on the RTX 3080. The count compares the fixed-32-lane translator with the counted-loop proof (`dba92a1`) and with the nested-loop proof (`1bd6050`). All nine additions were compute pipelines. The public reproduction checks the new proof against its immediate predecessor with a synthetic shader and a CPU oracle. [Source patches and reproduction](../repro/shader/README.md)

## Why the loop proof matters

A guest Wave64 workgroup can contain several logical waves. On a Wave32 adapter the translator may lower each independent logical wave to two host waves, with shared storage and synchronization for operations that cross the halves. The compiler must establish that a logical wave can make progress independently before partitioning a multi-wave group that writes output. A backward branch alone supplies no such evidence. [DirectX wave intrinsics](https://github.com/microsoft/DirectXShaderCompiler/wiki/Wave-Intrinsics)

- The counted-loop proof traces the latch comparison to the loop header's SSA phi and verifies that the backedge feeds the incremented value back into the counter. It recognizes a fixed-trip unsigned loop. It also supplies the basis for checking a signed increasing counter against a bound invariant within the loop.
- The nested proof handles an inner signed counted loop and an outer bit scan. The outer loop computes the index of the least significant set bit, exits when only that bit remains, and otherwise clears that same bit on the backedge. Each backward edge must match a supported proof. The compiler can continue to refuse polling loops and loops whose progress it cannot establish.
- The synthetic regression forces a fixed Wave32 target for translation, checks that the program partitions into two logical waves, and compares each of 256 output dwords from two 128-thread workgroups against a CPU oracle for visited bits and the ordered inner-loop results. Three negative variants clear a different bit, hold the counter steady, or change the bound on the backedge.

## Opening-scene sample

The sample is the same 36 unique shaders named as missing pipelines in one prior world-entry capture. Each candidate was translated at fixed Wave32 and counted as recovered when both the SDK validator and the RTX 3080 driver accepted the shader in the pipeline test.

| Translator | Validated pipelines | Multi-Wave64 group refusals | Other unresolved |
| --- | ---: | ---: | ---: |
| Before counted-loop proof (`314ad78`) | 4 / 36 | 28 | 4 |
| Counted-loop proof (`dba92a1`) | 6 / 36 | 26 | 4 |
| Nested-loop proof (`1bd6050`) | 15 / 36 | 17 | 4 |

The four other failures were one whole-wave section and three descriptor cases. Pipeline creation establishes driver acceptance. The CPU oracle establishes output correctness for the synthetic workload. Output correctness, recovered dispatch counts and frame-rate gains for the nine additional opening shaders remain unmeasured. Two warm runs of the combined candidate reached 40 world intervals with pending pipeline builds and nearly black captures, so those measurements cannot isolate the loop change.

## Other shader results in the series

| Change | Evidence |
| --- | --- |
| Ordered half-precision sums across split waves | The synthetic 256-thread case checks both halves, four logical waves, rounding after every add and preservation of the high word. A second case has 41 active lanes and checks the inactive outputs as well. The corresponding opening shader passed SDK validation and pipeline creation. |
| Cooperative Wave64 for shared local data storage (LDS) | Synthetic shared-counter and masked-export tests passed. A 512-thread opening BVH histogram pipeline passed on the RTX 3080, increasing the BVH library's accepted pipelines from 47 to 48 of 52. |
| Proven lane-local first-lane reads | The translator checks uniform reads and proves when both the EXEC mask and all uses confine a read to one thread. It also checks that LDS accesses within a barrier phase are confined to that thread or disjoint by dword. An opening exposure kernel matched all eight output float components of an independent CPU model across 33 histogram inputs. Downstream exposure consumption in the live scene remains unverified. |
| Device fences and coherent access | A 16-workgroup synthetic publication test checks the final counter and data payloads after preserving the device fence and using coherent UAV accesses. One isolated hierarchy dispatch subsequently completed in the runtime. |
| Per-wave lane-zero mask proof | A negative test substitutes group-thread ID for wave-local lane ID, allowing later waves to have empty masks. The opening BVH radix pass matched a CPU stable radix pass on seven input cases with guard regions checked. |
| Direct pixel barycentrics | A triangle with unequal clip-space W checks all four components at 256 pixel centers against distinct perspective and linear weights. Three captured pixel programs passed pipeline creation. One also passed a test linking it with its captured vertex stage. |
| SCC after branching on EXEC | The translator retains the scalar condition implied by a branch on the exact updated EXEC mask when the taken edge uniquely determines it. A 32-output synthetic loop exit matched its reference on the RTX 3080 and WARP. Two captured compute pipelines passed validation and creation. |

OpenAI Codex assisted in developing and testing these changes and preparing the reproduction. The patch series continues the VIctory source under GPL-3.0-or-later. [Public console-flow base](https://github.com/r4tedx/VIctory/commit/5a11cf4814436f978b7b989c8f9c113aba341f87) · [License](https://github.com/r4tedx/VIctory/blob/5a11cf4814436f978b7b989c8f9c113aba341f87/LICENSE)
