from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from .MemoryMap import (
    get_flag_data_for_event_key,
    get_memory_mapped_event_keys,
    is_event_set_in_memory,
)


@dataclass(frozen=True)
class MemoryEventScanResult:
    dump_path: Path
    event_key: str
    is_set: bool
    requirement_count: int
    notes: str


def read_binary_file(file_path: Path) -> bytes:
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find memory dump: {file_path}")

    return file_path.read_bytes()


def scan_memory_dump(
    dump_path: Path,
    memory_data: bytes,
    event_keys: list[str],
) -> list[MemoryEventScanResult]:
    results: list[MemoryEventScanResult] = []

    for event_key in event_keys:
        event_flag = get_flag_data_for_event_key(event_key)

        if event_flag is None:
            raise KeyError(f"Unknown event key: {event_key}")

        is_set = is_event_set_in_memory(
            event_key=event_key,
            memory_data=memory_data,
        )

        results.append(
            MemoryEventScanResult(
                dump_path=dump_path,
                event_key=event_key,
                is_set=is_set,
                requirement_count=len(event_flag.memory_requirements),
                notes=event_flag.notes,
            )
        )

    return results


def print_scan_results(
    dump_path: Path,
    results: list[MemoryEventScanResult],
    show_all: bool,
) -> None:
    detected_results = [
        result
        for result in results
        if result.is_set
    ]

    clear_results = [
        result
        for result in results
        if not result.is_set
    ]

    print()
    print(f"Dump: {dump_path}")
    print(f"Mapped events checked: {len(results)}")
    print(f"Detected mapped events: {len(detected_results)}")

    if detected_results:
        print()
        print("Detected mapped events:")

        for result in detected_results:
            print(
                "- "
                f"{result.event_key} "
                f"({result.requirement_count} memory requirement(s))"
            )

    if show_all and clear_results:
        print()
        print("Clear mapped events:")

        for result in clear_results:
            print(
                "- "
                f"{result.event_key} "
                f"({result.requirement_count} memory requirement(s))"
            )


def write_scan_csv(
    output_path: Path,
    all_results: list[MemoryEventScanResult],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "dump_file",
                "event_key",
                "is_set",
                "memory_requirement_count",
                "notes",
            ]
        )

        for result in all_results:
            writer.writerow(
                [
                    str(result.dump_path),
                    result.event_key,
                    result.is_set,
                    result.requirement_count,
                    result.notes,
                ]
            )

    print()
    print(f"Wrote memory event scan results to: {output_path}")


def scan_memory_events(
    dump_paths: list[Path],
    event_key_filter: list[str],
    show_all: bool,
    output_csv: Path | None,
) -> None:
    if not dump_paths:
        raise ValueError("At least one memory dump is required.")

    mapped_event_keys = sorted(get_memory_mapped_event_keys())

    if event_key_filter:
        unknown_event_keys = set(event_key_filter) - set(mapped_event_keys)

        if unknown_event_keys:
            raise ValueError(
                "Requested event key is not memory mapped: "
                f"{', '.join(sorted(unknown_event_keys))}"
            )

        event_keys = sorted(event_key_filter)
    else:
        event_keys = mapped_event_keys

    print("Pokemon HGSS memory event scanner")
    print(f"Memory dumps: {len(dump_paths)}")
    print(f"Mapped events available: {len(mapped_event_keys)}")
    print(f"Mapped events selected: {len(event_keys)}")

    all_results: list[MemoryEventScanResult] = []

    for dump_path in dump_paths:
        memory_data = read_binary_file(dump_path)

        print()
        print(f"Loaded dump: {dump_path}")
        print(f"Dump size: {len(memory_data)} bytes")

        results = scan_memory_dump(
            dump_path=dump_path,
            memory_data=memory_data,
            event_keys=event_keys,
        )

        all_results.extend(results)

        print_scan_results(
            dump_path=dump_path,
            results=results,
            show_all=show_all,
        )

    if output_csv is not None:
        write_scan_csv(
            output_path=output_csv,
            all_results=all_results,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan HGSS memory dumps for mapped Archipelago event keys."
    )

    parser.add_argument(
        "memory_dumps",
        nargs="+",
        type=Path,
        help="Memory dump files to scan.",
    )

    parser.add_argument(
        "--event-key",
        action="append",
        default=[],
        help=(
            "Only scan one mapped event key. "
            "Can be used multiple times."
        ),
    )

    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show both detected and clear mapped events.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV output path for scan results.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scan_memory_events(
        dump_paths=args.memory_dumps,
        event_key_filter=args.event_key,
        show_all=args.show_all,
        output_csv=args.output_csv,
    )


if __name__ == "__main__":
    main()