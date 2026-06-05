from __future__ import annotations

import argparse
import csv
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


@dataclass(frozen=True)
class ProbeResult:
    dump_path: Path
    candidate: BitCandidate
    byte_value: int
    bit_value: int


def parse_int(value: str) -> int:
    return int(value, 0)


def format_hex(value: int, width: int = 2) -> str:
    return f"0x{value:0{width}X}"


def read_binary_file(file_path: Path) -> bytes:
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find memory dump: {file_path}")

    return file_path.read_bytes()


def read_candidate_csv(csv_path: Path) -> list[BitCandidate]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find candidate CSV: {csv_path}")

    candidates: list[BitCandidate] = []

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

            candidates.append(
                BitCandidate(
                    offset=offset,
                    bit=bit,
                    bit_mask=bit_mask,
                )
            )

    return candidates


def probe_dump(
    dump_path: Path,
    dump_data: bytes,
    candidates: list[BitCandidate],
) -> list[ProbeResult]:
    results: list[ProbeResult] = []

    for candidate in candidates:
        if candidate.offset >= len(dump_data):
            raise ValueError(
                "Candidate offset is outside the memory dump. "
                f"Offset: {candidate.offset}, "
                f"dump size: {len(dump_data)}, "
                f"dump: {dump_path}"
            )

        byte_value = dump_data[candidate.offset]
        bit_value = (byte_value >> candidate.bit) & 1

        results.append(
            ProbeResult(
                dump_path=dump_path,
                candidate=candidate,
                byte_value=byte_value,
                bit_value=bit_value,
            )
        )

    return results


def filter_results(
    results: list[ProbeResult],
    only_set: bool,
    only_clear: bool,
) -> list[ProbeResult]:
    if only_set and only_clear:
        raise ValueError("Use either --only-set or --only-clear, not both.")

    if only_set:
        return [
            result
            for result in results
            if result.bit_value == 1
        ]

    if only_clear:
        return [
            result
            for result in results
            if result.bit_value == 0
        ]

    return results


def print_probe_results(
    dump_path: Path,
    results: list[ProbeResult],
    max_results: int,
) -> None:
    set_count = sum(
        1
        for result in results
        if result.bit_value == 1
    )

    clear_count = sum(
        1
        for result in results
        if result.bit_value == 0
    )

    print()
    print(f"Dump: {dump_path}")
    print(f"Candidate bits shown: {len(results)}")
    print(f"Set bits: {set_count}")
    print(f"Clear bits: {clear_count}")

    if not results:
        return

    print()
    print(f"First {min(max_results, len(results))} probe results:")

    for result in results[:max_results]:
        candidate = result.candidate

        print(
            "- "
            f"Offset {format_hex(candidate.offset, 8)}, "
            f"bit {candidate.bit}, "
            f"mask {format_hex(candidate.bit_mask)}: "
            f"byte {format_hex(result.byte_value)} -> "
            f"bit {result.bit_value}"
        )


def write_probe_csv(
    output_path: Path,
    all_results: list[ProbeResult],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "dump_file",
                "offset_decimal",
                "offset_hex",
                "bit",
                "bit_mask_hex",
                "byte_value_hex",
                "bit_value",
            ]
        )

        for result in all_results:
            candidate = result.candidate

            writer.writerow(
                [
                    str(result.dump_path),
                    candidate.offset,
                    format_hex(candidate.offset, 8),
                    candidate.bit,
                    format_hex(candidate.bit_mask),
                    format_hex(result.byte_value),
                    result.bit_value,
                ]
            )

    print()
    print(f"Wrote probe results to: {output_path}")


def probe_candidates(
    candidate_csv: Path,
    dump_paths: list[Path],
    max_results: int,
    only_set: bool,
    only_clear: bool,
    output_csv: Path | None,
) -> None:
    if not dump_paths:
        raise ValueError("At least one memory dump is required.")

    candidates = read_candidate_csv(candidate_csv)

    print("Pokemon HGSS memory candidate probe")
    print(f"Candidate CSV: {candidate_csv}")
    print(f"Candidates loaded: {len(candidates)}")
    print(f"Memory dumps: {len(dump_paths)}")

    all_filtered_results: list[ProbeResult] = []

    for dump_path in dump_paths:
        dump_data = read_binary_file(dump_path)

        print()
        print(f"Loaded dump: {dump_path}")
        print(f"Dump size: {len(dump_data)} bytes")

        results = probe_dump(
            dump_path=dump_path,
            dump_data=dump_data,
            candidates=candidates,
        )

        filtered_results = filter_results(
            results=results,
            only_set=only_set,
            only_clear=only_clear,
        )

        all_filtered_results.extend(filtered_results)

        print_probe_results(
            dump_path=dump_path,
            results=filtered_results,
            max_results=max_results,
        )

    if output_csv is not None:
        write_probe_csv(
            output_path=output_csv,
            all_results=all_filtered_results,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe candidate HGSS memory bits in one or more memory dumps."
        )
    )

    parser.add_argument(
        "candidate_csv",
        type=Path,
        help="Candidate CSV produced by MemoryCandidates.py.",
    )

    parser.add_argument(
        "memory_dumps",
        nargs="+",
        type=Path,
        help="Memory dump files to probe.",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of probe results to print per dump.",
    )

    parser.add_argument(
        "--only-set",
        action="store_true",
        help="Only show candidates whose bit value is 1 in the dump.",
    )

    parser.add_argument(
        "--only-clear",
        action="store_true",
        help="Only show candidates whose bit value is 0 in the dump.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV output path for probe results.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    probe_candidates(
        candidate_csv=args.candidate_csv,
        dump_paths=args.memory_dumps,
        max_results=args.max_results,
        only_set=args.only_set,
        only_clear=args.only_clear,
        output_csv=args.output_csv,
    )


if __name__ == "__main__":
    main()