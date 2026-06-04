from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ByteChange:
    offset: int
    before: int
    after: int

    @property
    def xor_mask(self) -> int:
        return self.before ^ self.after


@dataclass(frozen=True)
class BitChange:
    offset: int
    bit: int
    before_bit: int
    after_bit: int

    @property
    def bit_mask(self) -> int:
        return 1 << self.bit


def read_binary_file(file_path: Path) -> bytes:
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find file: {file_path}")

    return file_path.read_bytes()


def parse_offset(value: str | None) -> int | None:
    if value is None:
        return None

    return int(value, 0)


def find_byte_changes(
    before_data: bytes,
    after_data: bytes,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> list[ByteChange]:
    if len(before_data) != len(after_data):
        raise ValueError(
            "Memory dump sizes do not match. "
            f"Before: {len(before_data)} bytes, "
            f"After: {len(after_data)} bytes."
        )

    start = start_offset if start_offset is not None else 0
    end = end_offset if end_offset is not None else len(before_data)

    if start < 0:
        raise ValueError("start offset cannot be negative.")

    if end < start:
        raise ValueError("end offset cannot be smaller than start offset.")

    if end > len(before_data):
        raise ValueError(
            "end offset is outside the memory dump. "
            f"End offset: {end}, dump size: {len(before_data)}."
        )

    changes: list[ByteChange] = []

    for offset in range(start, end):
        before_byte = before_data[offset]
        after_byte = after_data[offset]

        if before_byte != after_byte:
            changes.append(
                ByteChange(
                    offset=offset,
                    before=before_byte,
                    after=after_byte,
                )
            )

    return changes


def find_bit_changes(byte_changes: list[ByteChange]) -> list[BitChange]:
    bit_changes: list[BitChange] = []

    for byte_change in byte_changes:
        for bit in range(8):
            before_bit = (byte_change.before >> bit) & 1
            after_bit = (byte_change.after >> bit) & 1

            if before_bit != after_bit:
                bit_changes.append(
                    BitChange(
                        offset=byte_change.offset,
                        bit=bit,
                        before_bit=before_bit,
                        after_bit=after_bit,
                    )
                )

    return bit_changes


def filter_bit_changes(
    bit_changes: list[BitChange],
    only_0_to_1: bool,
    only_1_to_0: bool,
) -> list[BitChange]:
    if only_0_to_1 and only_1_to_0:
        raise ValueError(
            "Use either --only-0-to-1-bits or --only-1-to-0-bits, not both."
        )

    if only_0_to_1:
        return [
            change
            for change in bit_changes
            if change.before_bit == 0 and change.after_bit == 1
        ]

    if only_1_to_0:
        return [
            change
            for change in bit_changes
            if change.before_bit == 1 and change.after_bit == 0
        ]

    return bit_changes


def format_hex(value: int, width: int = 2) -> str:
    return f"0x{value:0{width}X}"


def print_byte_changes(
    byte_changes: list[ByteChange],
    max_results: int,
) -> None:
    print()
    print(f"Changed bytes in selected range: {len(byte_changes)}")

    if not byte_changes:
        return

    print()
    print(f"First {min(max_results, len(byte_changes))} byte changes:")

    for change in byte_changes[:max_results]:
        print(
            f"- Offset {format_hex(change.offset, 8)}: "
            f"{format_hex(change.before)} -> {format_hex(change.after)} "
            f"(xor {format_hex(change.xor_mask)})"
        )


def print_bit_changes(
    bit_changes: list[BitChange],
    max_results: int,
) -> None:
    print()
    print(f"Changed bits after filters: {len(bit_changes)}")

    if not bit_changes:
        return

    print()
    print(f"First {min(max_results, len(bit_changes))} bit changes:")

    for change in bit_changes[:max_results]:
        print(
            f"- Offset {format_hex(change.offset, 8)}, "
            f"bit {change.bit}, "
            f"mask {format_hex(change.bit_mask)}: "
            f"{change.before_bit} -> {change.after_bit}"
        )


def write_csv(
    output_csv_path: Path,
    bit_changes: list[BitChange],
) -> None:
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    with output_csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "offset_decimal",
                "offset_hex",
                "bit",
                "bit_mask_hex",
                "before_bit",
                "after_bit",
            ]
        )

        for change in bit_changes:
            writer.writerow(
                [
                    change.offset,
                    format_hex(change.offset, 8),
                    change.bit,
                    format_hex(change.bit_mask),
                    change.before_bit,
                    change.after_bit,
                ]
            )

    print()
    print(f"Wrote filtered bit changes to: {output_csv_path}")


def compare_memory_dumps(
    before_path: Path,
    after_path: Path,
    max_results: int,
    start_offset: int | None,
    end_offset: int | None,
    only_0_to_1_bits: bool,
    only_1_to_0_bits: bool,
    output_csv_path: Path | None,
) -> None:
    before_data = read_binary_file(before_path)
    after_data = read_binary_file(after_path)

    print("Pokemon HGSS memory diff helper")
    print(f"Before file: {before_path}")
    print(f"After file:  {after_path}")
    print(f"Before size: {len(before_data)} bytes")
    print(f"After size:  {len(after_data)} bytes")

    if start_offset is not None or end_offset is not None:
        print(
            "Selected range: "
            f"{format_hex(start_offset or 0, 8)} to "
            f"{format_hex(end_offset if end_offset is not None else len(before_data), 8)}"
        )

    if only_0_to_1_bits:
        print("Bit filter: only 0 -> 1 changes")

    if only_1_to_0_bits:
        print("Bit filter: only 1 -> 0 changes")

    byte_changes = find_byte_changes(
        before_data,
        after_data,
        start_offset,
        end_offset,
    )

    bit_changes = find_bit_changes(byte_changes)
    filtered_bit_changes = filter_bit_changes(
        bit_changes,
        only_0_to_1_bits,
        only_1_to_0_bits,
    )

    print_byte_changes(byte_changes, max_results)
    print_bit_changes(filtered_bit_changes, max_results)

    if output_csv_path is not None:
        write_csv(output_csv_path, filtered_bit_changes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two HGSS memory/save dumps and show changed bytes/bits. "
            "This is a research helper for finding event flags."
        )
    )

    parser.add_argument(
        "before",
        type=Path,
        help="Binary dump from before the event.",
    )

    parser.add_argument(
        "after",
        type=Path,
        help="Binary dump from after the event.",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of byte/bit changes to print.",
    )

    parser.add_argument(
        "--start-offset",
        type=parse_offset,
        default=None,
        help=(
            "Start offset to compare. Accepts decimal or hex, "
            "for example 1234 or 0x00110000."
        ),
    )

    parser.add_argument(
        "--end-offset",
        type=parse_offset,
        default=None,
        help=(
            "End offset to compare, exclusive. Accepts decimal or hex, "
            "for example 4096 or 0x00120000."
        ),
    )

    parser.add_argument(
        "--only-0-to-1-bits",
        action="store_true",
        help="Only show bit changes where the bit changed from 0 to 1.",
    )

    parser.add_argument(
        "--only-1-to-0-bits",
        action="store_true",
        help="Only show bit changes where the bit changed from 1 to 0.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV output path for filtered bit changes.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compare_memory_dumps(
        before_path=args.before,
        after_path=args.after,
        max_results=args.max_results,
        start_offset=args.start_offset,
        end_offset=args.end_offset,
        only_0_to_1_bits=args.only_0_to_1_bits,
        only_1_to_0_bits=args.only_1_to_0_bits,
        output_csv_path=args.output_csv,
    )


if __name__ == "__main__":
    main()