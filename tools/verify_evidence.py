"""Validate the published VIctory archives and recompute their summaries."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
from statistics import mean, median
from zipfile import ZIP_DEFLATED, ZipFile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_bytes(data, record):
    require(len(data) == record["size_bytes"], f"Size mismatch for {record['file']}")
    require(sha256(data).hexdigest() == record["sha256"], f"SHA-256 mismatch for {record['file']}")
    return data


def check_nested_wave(data):
    for run in data["runs"]:
        intervals = run["intervals_ms"]
        size = len(intervals)
        require(0 < size <= 40 and size == run["interval_count"], "Invalid timing sample size")
        require(all(value > 0 for value in intervals), "Nonpositive present interval")
        require(round(median(intervals), 1) == run["median_ms"], "Unexpected median")
        require(round(mean(intervals), 1) == run["mean_ms"], "Unexpected mean")
        require(round(sorted(intervals)[ceil(0.95 * size) - 1], 1) == run["p95_ms"], "Unexpected p95")
    programs = data["anonymous_program_outcomes"]
    ids = {row["program"] for row in programs}
    require(len(programs) == 36 and ids == set(range(1, 37)), "Invalid census population")
    for stage in data["shader_census"]:
        outcomes = Counter(row[stage["translator"]] for row in programs)
        require(outcomes.pop("validated_pipeline", 0) == stage["validated_pipelines"], "Pipeline count mismatch")
        require(dict(outcomes) == stage["refusals_by_reason"], "Refusal reason counts mismatch")
        require(sum(outcomes.values()) == stage["unresolved"], "Unresolved count mismatch")
        require(len(programs) == stage["sampled_programs"], "Census total mismatch")


def check_bvh(data):
    for build in data["constructor_counts"]:
        total = build["matched_dispatches"]
        changed = build["dispatches_with_selected_field_change"]
        preserved = build["dispatches_with_all_selected_fields_preserved"]
        require(total == changed + preserved, "Constructor count mismatch")
        for count in build["changes_by_header_word"].values():
            require(0 <= count <= changed, "Field change count exceeds total changed dispatches")
    fixture = data["fixture_index_range"]
    limit = fixture["primitive_count"]
    missing = fixture["missing_valid_indices"]
    out_of_range = fixture["out_of_range_count"]
    require(fixture["valid_index_max"] == limit - 1, "Unexpected valid index range")
    require(
        fixture["index_count"] == fixture["unique_indices"] == limit,
        "Unexpected fixture index count",
    )
    require(missing == out_of_range, "Out-of-range and missing index counts differ")
    require(fixture["out_of_range_value_min"] >= limit, "Unexpected out-of-range minimum")
    require(fixture["out_of_range_value_max"] >= fixture["out_of_range_value_min"], "Invalid index range")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    args = parser.parse_args()
    manifest = json.loads((args.directory / "evidence-manifest.json").read_bytes())
    checks = {"nested-wave-opening": check_nested_wave, "bvh-constructor": check_bvh}
    names = [record["experiment"] for record in manifest["archives"]]
    require(sorted(names) == sorted(checks), "Unexpected archive set")
    for record in manifest["archives"]:
        name = record["experiment"]
        require(record["file"] == f"{name}.zip", "Unexpected archive name")
        archive = args.directory / record["file"]
        checked_bytes(archive.read_bytes(), record)
        members = record["members"]
        require([member["file"] for member in members] == [f"{name}.json"], "Unexpected manifest members")
        with ZipFile(archive) as zipped:
            require(zipped.namelist() == [f"{name}.json"], "Unexpected ZIP members")
            require(zipped.getinfo(f"{name}.json").compress_type == ZIP_DEFLATED, "Unexpected compression")
            data = json.loads(checked_bytes(zipped.read(f"{name}.json"), members[0]))
        require(data["schema_version"] == manifest["schema_version"], "Schema version mismatch")
        require(data["credit"] == manifest["credit"], "Credit mismatch")
        checks[name](data)
        print(f"Verified {record['file']}")


if __name__ == "__main__":
    main()
