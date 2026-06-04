from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BitCandidate:
    offset: int
    bit: int
    bit_mask: int

    @property
    def key(self) -> tuple[int, int]:
        return self.offset, self.bit


def parse_int(value: str) -> int:
    return int(value, 0)


def format_hex(value: int, width: int = 2) -> str:
    return f"0x{value:0{width}X}"


def read_candidate_csv(csv_path: Path) -> set[BitCandidate]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find CSV file: {csv_path}")

    candidates: set[BitCandidate] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        required_columns = {
            "offset_decimal",
            "bit",
            "bit_mask_hex",
        }

        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            raise ValueError(
                f"{csv_path} is missing required columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        for row in reader:
            offset = parse_int(row["offset_decimal"])
            bit = parse_int(row["bit"])
            bit_mask = parse_int(row["bit_mask_hex"])

            candidates.add(
                BitCandidate(
                    offset=offset,
                    bit=bit,
                    bit_mask=bit_mask,
                )
            )

    return candidates


def collect_candidate_counts(
    csv_paths: list[Path],
) -> tuple[Counter[BitCandidate], dict[BitCandidate, list[Path]]]:
    candidate_counts: Counter[BitCandidate] = Counter()
    candidate_sources: dict[BitCandidate, list[Path]] = defaultdict(list)

    for csv_path in csv_paths:
        candidates = read_candidate_csv(csv_path)

        for candidate in candidates:
            candidate_counts[candidate] += 1
            candidate_sources[candidate].append(csv_path)

    return candidate_counts, candidate_sources


def filter_candidates(
    candidate_counts: Counter[BitCandidate],
    file_count: int,
    min_count: int,
    common_only: bool,
) -> list[tuple[BitCandidate, int]]:
    required_count = file_count if common_only else min_count

    filtered_candidates = [
        (candidate, count)
        for candidate, count in candidate_counts.items()
        if count >= required_count
    ]

    return sorted(
        filtered_candidates,
        key=lambda candidate_and_count: (
            -candidate_and_count[1],
            candidate_and_count[0].offset,
            candidate_and_count[0].bit,
        ),
    )


def print_candidates(
    candidates: list[tuple[BitCandidate, int]],
    file_count: int,
    max_results: int,
) -> None:
    print()
    print(f"Candidate bits after filtering: {len(candidates)}")

    if not candidates:
        return

    print()
    print(f"First {min(max_results, len(candidates))} candidates:")

    for candidate, count in candidates[:max_results]:
        print(
            "- "
            f"Offset {format_hex(candidate.offset, 8)}, "
            f"bit {candidate.bit}, "
            f"mask {format_hex(candidate.bit_mask)} "
            f"appeared in {count}/{file_count} files"
        )


def write_candidates_csv(
    output_path: Path,
    candidates: list[tuple[BitCandidate, int]],
    file_count: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "offset_decimal",
                "offset_hex",
                "bit",
                "bit_mask_hex",
                "appeared_in_files",
                "total_files",
            ]
        )

        for candidate, count in candidates:
            writer.writerow(
                [
                    candidate.offset,
                    format_hex(candidate.offset, 8),
                    candidate.bit,
                    format_hex(candidate.bit_mask),
                    count,
                    file_count,
                ]
            )

    print()
    print(f"Wrote candidate summary to: {output_path}")


def compare_candidate_csvs(
    csv_paths: list[Path],
    min_count: int,
    common_only: bool,
    max_results: int,
    output_csv: Path | None,
) -> None:
    if not csv_paths:
        raise ValueError("At least one CSV file is required.")

    if min_count < 1:
        raise ValueError("--min-count must be at least 1.")

    candidate_counts, _candidate_sources = collect_candidate_counts(csv_paths)

    candidates = filter_candidates(
        candidate_counts=candidate_counts,
        file_count=len(csv_paths),
        min_count=min_count,
        common_only=common_only,
    )

    print("Pokemon HGSS memory candidate helper")
    print(f"Input CSV files: {len(csv_paths)}")
    print(f"Unique candidate bits: {len(candidate_counts)}")

    if common_only:
        print("Filter: candidates appearing in every file")
    else:
        print(f"Filter: candidates appearing in at least {min_count} file(s)")

    print_candidates(
        candidates=candidates,
        file_count=len(csv_paths),
        max_results=max_results,
    )

    if output_csv is not None:
        write_candidates_csv(
            output_path=output_csv,
            candidates=candidates,
            file_count=len(csv_paths),
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare HGSS memory research CSV files and find bit changes "
            "that appear consistently across multiple tests."
        )
    )

    parser.add_argument(
        "csv_files",
        nargs="+",
        type=Path,
        help="CSV files produced by MemoryResearch.py --output-csv.",
    )

    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Only show candidates that appear in at least this many files.",
    )

    parser.add_argument(
        "--common-only",
        action="store_true",
        help="Only show candidates that appear in every input CSV file.",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of candidates to print.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV output path for the candidate summary.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compare_candidate_csvs(
        csv_paths=args.csv_files,
        min_count=args.min_count,
        common_only=args.common_only,
        max_results=args.max_results,
        output_csv=args.output_csv,
    )


if __name__ == "__main__":
    main()