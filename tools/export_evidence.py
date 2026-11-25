"""Export allow-listed measurements from the archived VIctory benchmark runs."""

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import re
from statistics import mean, median
import struct
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


CREDIT = "Research and evidence extraction by OpenAI Codex"
HOST = "NVIDIA GeForce RTX 3080"
WORLD = re.compile(r"world's first frame .*?frame=(\d+)")
PRESENT = re.compile(r"present token=(\d+)")
PIPELINE_QUEUE = re.compile(r"\((\d+) being made\)")
CENSUS_RECORD = re.compile(
    r"^.*[\\/]([0-9a-f]{16})\.dxbc@0x[0-9a-f]+ \w+"
    r"(?: at 0x[0-9a-f]+)?  (.+)$"
)
HEADER_RECORD = re.compile(
    r'BVH header origin stage="(fenced|after_construct)" '
    r'src=(\d+) dst=(\d+) stride=0 reset=\d+ .*? '
    r'header=Some\(\(\d+, \d+, \[([\d, ]+)\]\)\)'
)
HEADER_FIELDS = (3, 13, 14, 15)
CENSUS_REASONS = {
    "emit: console wave64 lanes in a group of more than 64 threads on a host without 64-lane waves": "multi_wave64",
    "emit: a whole-wave section of a wave64 on a host without 64-lane waves": "whole_wave_section",
    "resources: a descriptor neither loaded nor built": "descriptor_provenance",
    "emit: a descriptor chosen by control flow": "descriptor_control_flow",
}


def run_log(root, suffix):
    logs = list(root.glob(f"????????-??????-???-*-{suffix}/stderr.log"))
    logs = [log for log in logs if log.parent.name.split("-", 4)[4] == suffix]
    if len(logs) != 1:
        raise ValueError(f"Expected one archived log for {suffix}, found {len(logs)}")
    return logs[0]


def require_revision(log, revision):
    metadata = json.loads(log.with_name("run.json").read_text(encoding="utf-8-sig"))
    if metadata["sourceRevision"] != revision or metadata["console"] != "series-x":
        raise ValueError("Unexpected source revision or console profile")


def opening_intervals(log, role, revision):
    require_revision(log, revision)
    presents = {}
    start = None
    queue = None
    device_removed = False
    with log.open(encoding="utf-8-sig", errors="replace") as stream:
        for line in stream:
            if match := WORLD.search(line):
                start = int(match[1])
            if match := PRESENT.search(line):
                timestamp = datetime.fromisoformat(line[:26])
                presents[int(match[1])] = timestamp
            if start is not None and (match := PIPELINE_QUEUE.search(line)):
                queue = int(match[1])
            if "host GPU device removed" in line:
                device_removed = True
    if start is None:
        raise ValueError(f"{role} never logged the first world frame")
    intervals = []
    for token in range(start, start + 40):
        if token not in presents or token + 1 not in presents:
            break
        elapsed = presents[token + 1] - presents[token]
        intervals.append(round(elapsed.total_seconds() * 1000, 3))
    if not intervals or any(value <= 0 for value in intervals):
        raise ValueError(f"No valid contiguous timing sample for {role}")
    return {
        "role": role,
        "source_revision": revision,
        "interval_count": len(intervals),
        "intervals_ms": intervals,
        "median_ms": round(median(intervals), 1),
        "p95_ms": round(sorted(intervals)[ceil(0.95 * len(intervals)) - 1], 1),
        "mean_ms": round(mean(intervals), 1),
        "last_report_pipeline_queue": queue,
        "device_removal_reported": device_removed,
    }


def census(log):
    validated = set()
    pipelines = set()
    refused = {}
    for line in log.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if match := CENSUS_RECORD.fullmatch(line):
            shader, outcome = match.groups()
            if outcome == "validated":
                validated.add(shader)
            elif outcome == "pipeline created":
                pipelines.add(shader)
            else:
                refused[shader] = CENSUS_REASONS[outcome]
    if validated != pipelines or pipelines & refused.keys():
        raise ValueError("Census records do not give one final outcome per container")
    return pipelines, refused


def nested_wave_evidence(root):
    directory = root / "opening-luminance-readback" / "opening-drop-census"
    census_cases = (
        ("original", "314ad78.log"),
        ("counted_loops", "counted-loop-results.log"),
        ("nested_loops", "nested-wave-loops.log"),
    )
    counts = []
    outcomes_by_program = {}
    for label, filename in census_cases:
        pipelines, refused = census(directory / filename)
        population = pipelines | refused.keys()
        if len(population) != 36 or (outcomes_by_program and population != outcomes_by_program.keys()):
            raise ValueError("Expected the same 36 observed drops in every census")
        for shader in population:
            outcomes_by_program.setdefault(shader, []).append(refused.get(shader, "validated_pipeline"))
        counts.append({
            "translator": label,
            "sampled_programs": len(population),
            "validated_pipelines": len(pipelines),
            "unresolved": len(refused),
            "refusals_by_reason": dict(Counter(refused.values())),
        })
    run_cases = (
        ("control", "e0672ae", "reconnected-e0672ae-control"),
        ("candidate", "1bd6050", "reconnected-nested-wave-candidate"),
        ("candidate_repeat", "1bd6050", "reconnected-nested-wave-repeat"),
    )
    runs = [
        opening_intervals(run_log(root, suffix), role, revision)
        for role, revision, suffix in run_cases
    ]
    return {
        "schema_version": 1,
        "credit": CREDIT,
        "gpu": HOST,
        "host_wave_lanes": 32,
        "console_profile": "Series X",
        "scheduling": "normal",
        "sample": "Up to 40 consecutive present intervals from the first world frame",
        "percentile_method": "nearest rank",
        "runs": runs,
        "census_scope": "Distinct missing-pipeline reports in one opening capture",
        "shader_census": counts,
        "anonymous_program_outcomes": [
            {"program": index, **dict(zip((label for label, _ in census_cases), outcomes))}
            for index, outcomes in enumerate(sorted(outcomes_by_program.values()), start=1)
        ],
    }


def bvh_constructor_counts(log, revision):
    require_revision(log, revision)
    pending = {}
    changes = Counter()
    compared = 0
    changed_any = 0
    with log.open(encoding="utf-8-sig", errors="replace") as stream:
        for line in stream:
            if not (match := HEADER_RECORD.search(line)):
                continue
            stage, source, scratch_counter, header = match.groups()
            key = (source, scratch_counter)
            words = [int(word) for word in header.split(",")]
            fields = tuple(words[index] for index in HEADER_FIELDS)
            if stage == "fenced":
                if key in pending:
                    raise ValueError("Unpaired before record for constructor dispatch")
                pending[key] = fields
                continue
            before = pending.pop(key)
            differing = [
                index
                for index, old, new in zip(HEADER_FIELDS, before, fields)
                if old != new
            ]
            compared += 1
            changed_any += bool(differing)
            changes.update(differing)
    if pending or not compared:
        raise ValueError(f"No complete constructor comparison for {revision}")
    return {
        "source_revision": revision,
        "matched_dispatches": compared,
        "dispatches_with_selected_field_change": changed_any,
        "dispatches_with_all_selected_fields_preserved": compared - changed_any,
        "changes_by_header_word": {str(index): changes[index] for index in HEADER_FIELDS},
    }


def bvh_fixture_range(directory):
    with (directory / "u0.bin").open("rb") as stream:
        header = struct.unpack("<4I", stream.read(16))
    count = header[3]
    data = (directory / "u7.bin").read_bytes()
    if count != 5021 or len(data) != 4 * count:
        raise ValueError("Unexpected BVH fixture index buffer length")
    values = [value for (value,) in struct.iter_unpack("<I", data)]
    invalid = [(position, value) for position, value in enumerate(values) if value >= count]
    if not invalid:
        raise ValueError("Expected out-of-range indices in the older BVH fixture")
    positions, out_of_range_values = zip(*invalid)
    return {
        "source_revision": "7c11041",
        "source_sample": "Pre-dispatch GPU readback, one constructor fixture",
        "primitive_count": count,
        "index_count": len(values),
        "unique_indices": len(set(values)),
        "valid_index_min": 0,
        "valid_index_max": count - 1,
        "missing_valid_indices": len(set(range(count)) - set(values)),
        "out_of_range_count": len(positions),
        "out_of_range_position_min": min(positions),
        "out_of_range_position_max": max(positions),
        "out_of_range_value_min": min(out_of_range_values),
        "out_of_range_value_max": max(out_of_range_values),
    }


def bvh_evidence(root):
    return {
        "schema_version": 1,
        "credit": CREDIT,
        "gpu": HOST,
        "console_profile": "Series X",
        "scheduling": "ordered diagnostic",
        "header_comparison": "Fenced and post-dispatch samples at stride zero",
        "header_words_compared": HEADER_FIELDS,
        "constructor_counts": [
            bvh_constructor_counts(run_log(root, "bvh-construct-before-after"), "7c11041"),
            bvh_constructor_counts(run_log(root, "current-bvh-construct-before-after"), "243a0b8"),
        ],
        "fixture_index_range": bvh_fixture_range(
            root / "opening-luminance-readback" / "constructor-fixtures-7c11041" / "case-0"
        ),
    }


def json_bytes(data):
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def package(output, experiment, data):
    payload = json_bytes(data)
    archive = output / f"{experiment}.zip"
    member = ZipInfo(f"{experiment}.json", date_time=(1980, 1, 1, 0, 0, 0))
    member.create_system = 3
    member.external_attr = 0o100644 << 16
    with ZipFile(archive, "w") as zipped:
        zipped.writestr(member, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
    archive_data = archive.read_bytes()
    return {
        "experiment": experiment,
        "file": archive.name,
        "size_bytes": len(archive_data),
        "sha256": sha256(archive_data).hexdigest(),
        "members": [{
            "file": member.filename,
            "size_bytes": len(payload),
            "sha256": sha256(payload).hexdigest(),
        }],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark_root", type=Path, help="Local archived Benchmarks directory")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    args = parser.parse_args()

    experiments = {
        "nested-wave-opening": nested_wave_evidence(args.benchmark_root),
        "bvh-constructor": bvh_evidence(args.benchmark_root),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "credit": CREDIT,
        "benchmark_dates": ["2026-11-25", "2026-11-26"],
        "gpu": HOST,
        "publication_inventory": {"gpu_driver_version": "32.0.16.1088"},
        "archives": [package(args.output, name, data) for name, data in experiments.items()],
    }
    (args.output / "evidence-manifest.json").write_bytes(json_bytes(manifest))


if __name__ == "__main__":
    main()
