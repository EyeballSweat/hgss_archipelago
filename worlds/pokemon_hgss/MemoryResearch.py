from __future__ import annotations

import argparse
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


def find_byte_changes(before_data: bytes, after_data: bytes) -> list[ByteChange]:
    if len(before_data) != len(after_data):
        raise ValueError(
            "Memory dump sizes do not match. "
            f"Before: {len(before_data)} bytes, "
            f"After: {len(after_data)} bytes."
        )

    changes: list[ByteChange] = []

    for offset, (before_byte, after_byte) in enumerate(
        zip(before_data, after_data)
    ):
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


def format_hex(value: int, width: int = 2) -> str:
    return f"0x{value:0{width}X}"


def print_byte_changes(
    byte_changes: list[ByteChange],
    max_results: int,
) -> None:
    print()
    print(f"Changed bytes: {len(byte_changes)}")

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
    print(f"Changed bits: {len(bit_changes)}")

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


def compare_memory_dumps(
    before_path: Path,
    after_path: Path,
    max_results: int,
) -> None:
    before_data = read_binary_file(before_path)
    after_data = read_binary_file(after_path)

    print("Pokemon HGSS memory diff helper")
    print(f"Before file: {before_path}")
    print(f"After file:  {after_path}")
    print(f"Before size: {len(before_data)} bytes")
    print(f"After size:  {len(after_data)} bytes")

    byte_changes = find_byte_changes(before_data, after_data)
    bit_changes = find_bit_changes(byte_changes)

    print_byte_changes(byte_changes, max_results)
    print_bit_changes(bit_changes, max_results)


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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compare_memory_dumps(
        before_path=args.before,
        after_path=args.after,
        max_results=args.max_results,
    )


if __name__ == "__main__":
    main()