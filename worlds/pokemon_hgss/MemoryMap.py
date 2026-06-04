from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventFlagData:
    event_key: str
    address: int | None
    bit_mask: int | None
    notes: str


# These are placeholders for now.
#
# Later, when we start researching HGSS memory/save flags, each event key will
# get a real RAM/save address and bit mask.
#
# Example future shape:
# EventFlagData(
#     event_key="defeated_falkner",
#     address=0x021XXXXX,
#     bit_mask=0x04,
#     notes="Set after Falkner battle reward sequence.",
# )
EVENT_FLAG_TABLE = (
    EventFlagData(
        "received_starter",
        None,
        None,
        "TODO: Find flag set after receiving the starter Pokemon.",
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
    return set(event_key_to_flag_data)