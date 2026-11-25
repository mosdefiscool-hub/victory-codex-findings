# Reproduce the nested Wave64 loop fix

This uses a publicly fetchable VIctory console-flow revision and a hand-written synthetic compute program. The GPU check needs Windows, Rust via rustup, the MSVC C++ build tools and Windows SDK, and a D3D12 Wave32 adapter. The DXIL check uses the SDK validator when available. On other hardware the fixed-Wave32 translation checks can still run. [Shader findings](../../reports/shader.md) · [Public base](https://github.com/r4tedx/VIctory/commit/5a11cf4814436f978b7b989c8f9c113aba341f87)

From the findings repository root in PowerShell, create a fresh checkout next to it and apply the three prerequisite patches in order. This reconstructs the `victory-shader` crate of the counted-loop control (`dba92a1`).

```powershell
$patches = (Resolve-Path ./repro/shader).Path
git init ../victory-shader-test
Set-Location ../victory-shader-test
git fetch --no-tags --depth 1 https://github.com/r4tedx/VIctory.git 5a11cf4814436f978b7b989c8f9c113aba341f87
git checkout --detach FETCH_HEAD
foreach ($patch in (Get-ChildItem "$patches/0[1-3]*.patch" | Sort-Object Name)) {
    git apply --check $patch.FullName
    if ($LASTEXITCODE -ne 0) { throw "Patch check failed for $($patch.Name)" }
    git apply $patch.FullName
    if ($LASTEXITCODE -ne 0) { throw "Could not apply $($patch.Name)" }
}
```

Apply only the regression test. The single test should fail with the translator refusing Wave64 in a group of more than 64 threads on a host without 64-lane waves. The assertion uses a forced Wave32 target and runs before any GPU dispatch.

```powershell
$fix = "$patches/04-nested-wave-progress.patch"
$testFile = 'crates/victory-shader/src/emit/split_tests.rs'
$testName = 'nested_bit_scan_and_counted_console_wave_loops_preserve_values'
git apply --include=$testFile $fix
cargo test --locked -p victory-shader --features host $testName -- --test-threads=1 --nocapture
```

Apply the implementation from the same patch and rerun. Check that the output contains `128 threads exact (split true)` for a Wave32 adapter. That line confirms the GPU ran the translated shader and matched the CPU oracle across two workgroups, for 256 dwords per adapter. Runs without a usable adapter can still pass the translation assertions.

```powershell
git apply --exclude=$testFile $fix
cargo test --locked -p victory-shader --features host $testName -- --test-threads=1 --nocapture
cargo test --locked -p victory-shader --features host -- --test-threads=1
```

To run the green suite without the before-and-after check, apply the entire fourth patch after patches 01 through 03. Set `VICTORY_TEST_ADAPTERS` to a substring of your adapter's name if you need to limit the hardware loop.

## Verified results

- The public revision fetched into a fresh shallow checkout, and the patches applied cleanly.
- The isolated regression failed on the counted-loop implementation with the expected refusal. With the implementation patch it passed and printed `128 threads exact (split true)` on the RTX 3080.
- The full shader suite passed 339 tests with 3 ignored on the patched public checkout.

The patches contain translator source and synthetic regression programs. Patch 01 reconstructs the preceding shader crate changes needed by this stack. Patches 02 and 03 restore the ordered half-sum and intervening shader fixes. Patch 04 is the nested-loop change. OpenAI Codex assisted in developing the changes and preparing the reproduction. Upstream notices and the GPL-3.0-or-later license apply. [VIctory license](https://github.com/r4tedx/VIctory/blob/5a11cf4814436f978b7b989c8f9c113aba341f87/LICENSE)
