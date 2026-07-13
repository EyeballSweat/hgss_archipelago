from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .MemoryMap import get_memory_mapped_event_keys


EXPECTED_FORMAT_VERSION = 1


@dataclass(frozen=True)
class BridgeEventState:
    event_key: str
    is_set: bool
    requirement_count: int
    notes: str


def is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_bridge_state_file(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find bridge state file: {file_path}")

    with file_path.open("r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    if not isinstance(data, dict):
        raise ValueError("Bridge state file must contain a JSON object.")

    return data


def validate_requirement_data(
    event_key: str,
    requirement_data: object,
    errors: list[str],
) -> None:
    if not isinstance(requirement_data, dict):
        errors.append(
            "Bridge requirement must be a JSON object: "
            f"{event_key}"
        )
        return

    address = requirement_data.get("address")
    bit_mask = requirement_data.get("bit_mask")
    byte_value = requirement_data.get("byte_value")
    is_set = requirement_data.get("is_set")

    if not is_integer(address) or address < 0:
        errors.append(
            "Bridge requirement has invalid address: "
            f"{event_key}"
        )

    if not is_integer(bit_mask) or bit_mask <= 0 or bit_mask > 0xFF:
        errors.append(
            "Bridge requirement has invalid bit mask: "
            f"{event_key}"
        )
    elif bit_mask & (bit_mask - 1) != 0:
        errors.append(
            "Bridge requirement should use a single-bit mask: "
            f"{event_key} 0x{bit_mask:02X}"
        )

    if not is_integer(byte_value) or byte_value < 0 or byte_value > 0xFF:
        errors.append(
            "Bridge requirement has invalid byte value: "
            f"{event_key}"
        )

    if not isinstance(is_set, bool):
        errors.append(
            "Bridge requirement has invalid is_set value: "
            f"{event_key}"
        )


def validate_bridge_state_data(data: dict[str, Any]) -> None:
    errors: list[str] = []

    format_version = data.get("format_version")

    if format_version != EXPECTED_FORMAT_VERSION:
        errors.append(
            "Unsupported bridge state format version. "
            f"Expected {EXPECTED_FORMAT_VERSION}, got {format_version}."
        )

    memory_domain = data.get("memory_domain")

    if not isinstance(memory_domain, str) or not memory_domain:
        errors.append("Bridge state has invalid or missing memory_domain.")

    frame_count = data.get("frame_count")

    if not is_integer(frame_count) or frame_count < 0:
        errors.append("Bridge state has invalid or missing frame_count.")

    event_states = data.get("event_states")

    if not isinstance(event_states, dict):
        errors.append("Bridge state has invalid or missing event_states.")
    else:
        mapped_event_keys = get_memory_mapped_event_keys()

        for event_key, event_data in event_states.items():
            if event_key not in mapped_event_keys:
                errors.append(
                    "Bridge state contains event key that is not memory mapped: "
                    f"{event_key}"
                )

            if not isinstance(event_data, dict):
                errors.append(
                    "Bridge event state must be a JSON object: "
                    f"{event_key}"
                )
                continue

            is_set = event_data.get("is_set")

            if not isinstance(is_set, bool):
                errors.append(
                    "Bridge event state has invalid is_set value: "
                    f"{event_key}"
                )

            notes = event_data.get("notes")

            if not isinstance(notes, str):
                errors.append(
                    "Bridge event state has invalid notes value: "
                    f"{event_key}"
                )

            requirements = event_data.get("requirements")

            if not isinstance(requirements, list) or not requirements:
                errors.append(
                    "Bridge event state has invalid or empty requirements: "
                    f"{event_key}"
                )
                continue

            for requirement_data in requirements:
                validate_requirement_data(
                    event_key=event_key,
                    requirement_data=requirement_data,
                    errors=errors,
                )

    if errors:
        error_text = "\n".join(
            f"- {error}"
            for error in errors
        )

        raise ValueError(
            "Pokemon HGSS memory bridge state validation failed:\n"
            f"{error_text}"
        )


def get_bridge_event_states(data: dict[str, Any]) -> list[BridgeEventState]:
    event_states = data["event_states"]

    return [
        BridgeEventState(
            event_key=event_key,
            is_set=event_data["is_set"],
            requirement_count=len(event_data["requirements"]),
            notes=event_data["notes"],
        )
        for event_key, event_data in sorted(event_states.items())
    ]

def get_completed_event_keys_from_bridge_state(
    bridge_state_path: Path,
) -> set[str]:
    data = load_bridge_state_file(bridge_state_path)
    validate_bridge_state_data(data)

    bridge_event_states = get_bridge_event_states(data)

    return {
        event_state.event_key
        for event_state in bridge_event_states
        if event_state.is_set
    }


def print_bridge_summary(
    bridge_state_path: Path,
    data: dict[str, Any],
    bridge_event_states: list[BridgeEventState],
    show_all: bool,
) -> None:
    detected_events = [
        event_state
        for event_state in bridge_event_states
        if event_state.is_set
    ]

    clear_events = [
        event_state
        for event_state in bridge_event_states
        if not event_state.is_set
    ]

    print("Pokemon HGSS memory bridge state reader")
    print(f"Bridge state: {bridge_state_path}")
    print(f"Format version: {data['format_version']}")
    print(f"Memory domain: {data['memory_domain']}")
    print(f"Frame count: {data['frame_count']}")
    print(f"Mapped events in bridge: {len(bridge_event_states)}")
    print(f"Detected mapped events: {len(detected_events)}")

    if detected_events:
        print()
        print("Detected mapped events:")

        for event_state in detected_events:
            print(
                "- "
                f"{event_state.event_key} "
                f"({event_state.requirement_count} memory requirement(s))"
            )

    if show_all and clear_events:
        print()
        print("Clear mapped events:")

        for event_state in clear_events:
            print(
                "- "
                f"{event_state.event_key} "
                f"({event_state.requirement_count} memory requirement(s))"
            )


def write_bridge_csv(
    output_path: Path,
    bridge_event_states: list[BridgeEventState],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "event_key",
                "is_set",
                "memory_requirement_count",
                "notes",
            ]
        )

        for event_state in bridge_event_states:
            writer.writerow(
                [
                    event_state.event_key,
                    event_state.is_set,
                    event_state.requirement_count,
                    event_state.notes,
                ]
            )

    print()
    print(f"Wrote memory bridge summary to: {output_path}")


def read_bridge_state(
    bridge_state_path: Path,
    show_all: bool,
    output_csv: Path | None,
) -> None:
    data = load_bridge_state_file(bridge_state_path)
    validate_bridge_state_data(data)

    bridge_event_states = get_bridge_event_states(data)

    print_bridge_summary(
        bridge_state_path=bridge_state_path,
        data=data,
        bridge_event_states=bridge_event_states,
        show_all=show_all,
    )

    if output_csv is not None:
        write_bridge_csv(
            output_path=output_csv,
            bridge_event_states=bridge_event_states,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read a Pokemon HGSS BizHawk memory bridge state file."
    )

    parser.add_argument(
        "bridge_state",
        type=Path,
        help="JSON bridge state file written by hgss_memory_bridge.lua.",
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
        help="Optional CSV output path for bridge summary.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    read_bridge_state(
        bridge_state_path=args.bridge_state,
        show_all=args.show_all,
        output_csv=args.output_csv,
    )


if __name__ == "__main__":
    main()