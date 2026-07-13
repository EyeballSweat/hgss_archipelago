from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryBitRequirement:
    address: int
    bit_mask: int
    notes: str


@dataclass(frozen=True)
class EventFlagData:
    event_key: str
    address: int | None
    bit_mask: int | None
    notes: str
    additional_requirements: tuple[MemoryBitRequirement, ...] = ()

    @property
    def memory_requirements(self) -> tuple[MemoryBitRequirement, ...]:
        requirements: list[MemoryBitRequirement] = []

        if self.address is not None and self.bit_mask is not None:
            requirements.append(
                MemoryBitRequirement(
                    address=self.address,
                    bit_mask=self.bit_mask,
                    notes="Primary memory requirement.",
                )
            )

        requirements.extend(self.additional_requirements)

        return tuple(requirements)

    @property
    def is_memory_mapped(self) -> bool:
        return bool(self.memory_requirements)


# Main RAM offsets are BizHawk domain offsets, not Nintendo DS absolute addresses.
#
# Most entries are placeholders for now.
#
# The received_starter mapping is tentative. It was found through repeated
# Main RAM diffing and probing:
# - clear before receiving a starter
# - clear after cancelling starter selection
# - set after choosing each of the three starters
# - remains set after walking around
# - remains set after save/reload
#
# Because this is still research-derived and not an official event flag, it
# currently requires two independent candidate bits to reduce false positives.
EVENT_FLAG_TABLE = (
    EventFlagData(
        "received_starter",
        0x00110B40,
        0x02,
        "Tentative Main RAM mapping for receiving any starter Pokemon.",
        (
            MemoryBitRequirement(
                0x00110B46,
                0x04,
                "Second required candidate bit for received_starter.",
            ),
        ),
    ),
    EventFlagData(
        "received_pokegear",
        None,
        None,
        "TODO: Find flag set after receiving the Pokegear.",
    ),
    EventFlagData(
        "received_running_shoes",
        None,
        None,
        "TODO: Find flag set after receiving Running Shoes.",
    ),
    EventFlagData(
        "received_map_card",
        None,
        None,
        "TODO: Find flag set after receiving the Map Card.",
    ),
    EventFlagData(
        "visited_mr_pokemon",
        None,
        None,
        "TODO: Find flag set after visiting Mr. Pokemon.",
    ),
    EventFlagData(
        "received_apricorn_box",
        None,
        None,
        "TODO: Find flag set after receiving the Apricorn Box.",
    ),
    EventFlagData(
        "cleared_sprout_tower",
        None,
        None,
        "TODO: Find flag set after clearing Sprout Tower.",
    ),
    EventFlagData(
        "defeated_falkner",
        None,
        None,
        "TODO: Find flag set after defeating Falkner.",
    ),
    EventFlagData(
        "received_togepi_egg",
        None,
        None,
        "TODO: Find flag set after receiving the Togepi Egg.",
    ),
    EventFlagData(
        "received_miracle_seed",
        None,
        None,
        "TODO: Find flag set after receiving Miracle Seed.",
    ),
    EventFlagData(
        "reached_union_cave_south_exit",
        None,
        None,
        "TODO: Decide whether this is a flag, map transition, or milestone.",
    ),
    EventFlagData(
        "cleared_slowpoke_well",
        None,
        None,
        "TODO: Find flag set after clearing Slowpoke Well.",
    ),
    EventFlagData(
        "defeated_bugsy",
        None,
        None,
        "TODO: Find flag set after defeating Bugsy.",
    ),
    EventFlagData(
        "cleared_farfetchd_puzzle",
        None,
        None,
        "TODO: Find flag set after clearing the Farfetch'd puzzle.",
    ),
    EventFlagData(
        "defeated_whitney",
        None,
        None,
        "TODO: Find flag set after defeating Whitney.",
    ),
    EventFlagData(
        "received_bicycle",
        None,
        None,
        "TODO: Find flag set after receiving the Bicycle.",
    ),
    EventFlagData(
        "received_radio_card",
        None,
        None,
        "TODO: Find flag set after receiving the Radio Card.",
    ),
    EventFlagData(
        "received_kenya",
        None,
        None,
        "TODO: Find flag set after receiving Kenya.",
    ),
    EventFlagData(
        "received_quick_claw",
        None,
        None,
        "TODO: Find flag set after receiving Quick Claw.",
    ),
    EventFlagData(
        "defeated_rival_burned_tower",
        None,
        None,
        "TODO: Find flag set after Burned Tower rival battle.",
    ),
    EventFlagData(
        "defeated_morty",
        None,
        None,
        "TODO: Find flag set after defeating Morty.",
    ),
    EventFlagData(
        "cleared_dance_theater",
        None,
        None,
        "TODO: Find flag set after clearing Dance Theater.",
    ),
    EventFlagData(
        "defeated_kimono_girls",
        None,
        None,
        "TODO: Find flag set after defeating Kimono Girls.",
    ),
    EventFlagData(
        "received_good_rod",
        None,
        None,
        "TODO: Find flag set after receiving Good Rod.",
    ),
    EventFlagData(
        "reached_amphy",
        None,
        None,
        "TODO: Decide whether this is a flag, map check, or story flag.",
    ),
    EventFlagData(
        "received_secretpotion",
        None,
        None,
        "TODO: Find flag set after receiving SecretPotion.",
    ),
    EventFlagData(
        "defeated_chuck",
        None,
        None,
        "TODO: Find flag set after defeating Chuck.",
    ),
    EventFlagData(
        "received_shuckle",
        None,
        None,
        "TODO: Find flag set after receiving Shuckle.",
    ),
    EventFlagData(
        "defeated_jasmine",
        None,
        None,
        "TODO: Find flag set after defeating Jasmine.",
    ),
    EventFlagData(
        "cleared_team_rocket_hq",
        None,
        None,
        "TODO: Find flag set after clearing Team Rocket HQ.",
    ),
    EventFlagData(
        "defeated_red_gyarados",
        None,
        None,
        "TODO: Find flag set after defeating/capturing Red Gyarados.",
    ),
    EventFlagData(
        "defeated_pryce",
        None,
        None,
        "TODO: Find flag set after defeating Pryce.",
    ),
    EventFlagData(
        "received_basement_key",
        None,
        None,
        "TODO: Find flag set after receiving Basement Key.",
    ),
    EventFlagData(
        "received_card_key",
        None,
        None,
        "TODO: Find flag set after receiving Card Key.",
    ),
    EventFlagData(
        "cleared_radio_tower",
        None,
        None,
        "TODO: Find flag set after clearing Radio Tower.",
    ),
    EventFlagData(
        "defeated_clair",
        None,
        None,
        "TODO: Find flag set after defeating Clair.",
    ),
    EventFlagData(
        "defeated_victory_road_rival",
        None,
        None,
        "TODO: Find flag set after Victory Road rival battle.",
    ),
)


event_key_to_flag_data = {
    event_flag.event_key: event_flag
    for event_flag in EVENT_FLAG_TABLE
}


def get_flag_data_for_event_key(event_key: str) -> EventFlagData | None:
    return event_key_to_flag_data.get(event_key)


def get_mapped_event_keys() -> set[str]:
    """Return every known event key.

    This keeps the old behaviour of this helper. Other validation code may use
    it to check that every GameChecks event has a MemoryMap entry, even if the
    memory address is still TODO.
    """

    return set(event_key_to_flag_data)


def get_memory_mapped_event_keys() -> set[str]:
    return {
        event_key
        for event_key, event_flag in event_key_to_flag_data.items()
        if event_flag.is_memory_mapped
    }


def is_event_set_in_memory(event_key: str, memory_data: bytes) -> bool:
    event_flag = get_flag_data_for_event_key(event_key)

    if event_flag is None:
        raise KeyError(f"Unknown event key: {event_key}")

    if not event_flag.is_memory_mapped:
        return False

    for requirement in event_flag.memory_requirements:
        if requirement.address >= len(memory_data):
            raise ValueError(
                "Memory requirement is outside the supplied memory data. "
                f"Event key: {event_key}, "
                f"address: 0x{requirement.address:08X}, "
                f"memory size: {len(memory_data)}"
            )

        byte_value = memory_data[requirement.address]

        if byte_value & requirement.bit_mask != requirement.bit_mask:
            return False

    return True