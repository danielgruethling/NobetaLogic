import sys
import json
import re
from typing import Dict, Set


def region_to_normalized_locations(region) -> str:
    return re.sub(r'_+', '_', region['name'].replace(' ', '_').replace('-', '_')
                  .replace('.', '').lower() + "_locations")


def json_to_ap_python(file_path):
    # Load the JSON data
    with open(file_path, 'r') as file:
        data = json.loads(file.read())

    # Generate locations.py
    locations_code = [
        "from typing import Dict, TYPE_CHECKING",
        "from BaseClasses import Location",
        "from Options import Toggle\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "class LWNLocation(Location):",
        "    game: str = \"Little Witch Nobeta\"\n",
        "    # override constructor to automatically mark event locations as such",
        "    def __init__(self, player: int, name=\"\", code=None, parent=None):",
        "        super(LWNLocation, self).__init__(player, name, code, parent)",
        "        self.event = code is None\n\n",
        "base_id = 1\n",
    ]

    lwn_locations = [
        "lwn_locations: Dict[str, str] = {",
    ]

    location_name_groups = [
        "location_name_groups = {",
    ]

    location_group_map: Dict[str, Set[str]] = {
        "Bosses": set(),
        "Lore": set(),
        "Item": set(),
        "Chest": set(),
        "Metal Gate": set(),
        "Barrier": set(),
        "Teleport": set(),
        "Event": set(),
    }

    append_locations_code = [
        "def add_location_to_region(location_name, location_id, group_name, region, world):",
        "    if (group_name == \"Metal Gate\"",
        "            and world.options.shortcut_gate_behaviour.value"
                                 f" == world.options.shortcut_gate_behaviour.option_vanilla):",
        "        return",
        "    elif (group_name == \"Barrier\"",
        "          and world.options.barrier_behaviour.value"
                                 " == world.options.barrier_behaviour.option_vanilla):",
        "        return",
        "    elif (group_name == \"Lore\"",
        "          and world.options.randomize_lore.value"
                                 f" == Toggle.option_false):",
        "        return",
        "    region.locations.append(LWNLocation("
                                 f"world.player, location_name, location_id, region))\n\n",
        "def append_locations(world: \"LWNWorld\"):",
    ]

    # Generate regions.py
    regions_code = [
        "from typing import Dict, Set",
        "from BaseClasses import Region\n\n",
        "class LWNRegion(Region):",
        "    game: str = \"Little Witch Nobeta\"\n\n",
    ]

    lwn_regions = [
        "lwn_regions: Dict[str, Set[str]] = {"
    ]

    # Generate rules.py
    rules_code = [
        "from typing import TYPE_CHECKING\n",
        "from .options import Toggle, LWNOptions",
        "from worlds.generic.Rules import set_rule",
        "from BaseClasses import CollectionState\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "def has_fire_or_thunder(state: CollectionState, player: int) -> bool:",
        "    return state.has_any([\"Fire\", \"Thunder\"], player)\n\n",
        "def has_wind_or_skip(state: CollectionState, world: \"LWNWorld\") -> bool:",
        "    return (state.has(\"Wind\", world.player) or",
        "            world.options.wind_requirements.value == "
        "world.options.wind_requirements.option_less_wind_requirements)",
        "\n",
        "def has_wind_or_damage_boost(state: CollectionState, world: \"LWNWorld\") -> bool:",
        "    return (state.has(\"Wind\", world.player) or",
        "            (world.options.wind_requirements.value == "
        "world.options.wind_requirements.option_less_wind_requirements and ",
        "            state.has(\"Fire\", world.player)))",
        "\n",
        "def barriers_always_open(options: LWNOptions) -> bool:",
        "    return options.barrier_behaviour.value == "
        "options.barrier_behaviour.option_always_open",
        "\n",
        "def gates_always_open(options: LWNOptions) -> bool:",
        "    return options.shortcut_gate_behaviour.value == "
        "options.shortcut_gate_behaviour.option_always_open",
        "\n",
        "def has_attack_magic(state: CollectionState, player: int) -> bool:",
        "    return state.has_group(\"Attack Magics\", player)",
        "\n",
        "def has_counter(state: CollectionState, player: int) -> bool:",
        "    return state.has(\"Mana Absorption\", player)",
        "\n",
        "def has_barrier(state: CollectionState, barrier: str, world: \"LWNWorld\") -> bool:",
        "    return state.has(barrier, world.player) or barriers_always_open(world.options)",
        "\n",
        "def has_gate(state: CollectionState, gate: str, world: \"LWNWorld\") -> bool:",
        "    return state.has(gate, world.player) or gates_always_open(world.options)",
        "\n",
        "def set_region_rules(world: \"LWNWorld\") -> None:",
        "    multiworld = world.multiworld",
        "    player = world.player",
        "    options = world.options",
        "",
    ]

    location_rules = []

    for region in data['regions']:
        if 'locations' in region and region['locations']:
            region_locations = region_to_normalized_locations(region)
            lwn_locations.append(f"    **{region_locations},")
            region_locations += ": Dict[str, str] = {"
            locations_code.append(f"{region_locations}")
            for location in region['locations']:
                if 'name' in location and 'group' in location:
                    locations_code.append(f"    \"{location['name']}\": \"{location['group']}\",")
                else:
                    locations_code.append(f"    \"{location['name']}\": \"Item\",")
                if 'rules' in location:
                    if 'group' in location:
                        if location['group'] == "Barrier":
                            location_rules.append(f"    if options.barrier_behaviour.value == options.barrier_behaviour.option_randomized:")
                            location_rules.append(f"        set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' or ', r"\n                 or ", location['rules'])
                            subbed_rule = re.sub(' and ', r"\n                 and ", subbed_rule)
                            location_rules.append(f"                 lambda state: {subbed_rule})")
                        elif location['group'] == "Metal Gate":
                            location_rules.append(f"    if options.shortcut_gate_behaviour.value == options.shortcut_gate_behaviour.option_randomized:")
                            location_rules.append(f"        set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' or ', r"\n                 or ", location['rules'])
                            subbed_rule = re.sub(' and ', r"\n                 and ", subbed_rule)
                            location_rules.append(f"                 lambda state: {subbed_rule})")
                        elif location['group'] == "Lore":
                            location_rules.append(f"    if world.options.randomize_lore.value == Toggle.option_true:")
                            location_rules.append(f"        set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' or ', r"\n                 or ", location['rules'])
                            subbed_rule = re.sub(' and ', r"\n                 and ", subbed_rule)
                            location_rules.append(f"                 lambda state: {subbed_rule})")
                        else:
                            location_rules.append(f"    set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' or ', r"\n             or ", location['rules'])
                            subbed_rule = re.sub(' and ', r"\n             and ", subbed_rule)
                            location_rules.append(f"             lambda state: {subbed_rule})")
                    else:
                        location_rules.append(f"    set_rule(multiworld.get_location(\"{location['name']}\", player),")
                        subbed_rule = re.sub(' or ', r"\n             or ", location['rules'])
                        subbed_rule = re.sub(' and ', r"\n             and ", subbed_rule)
                        location_rules.append(f"             lambda state: {subbed_rule})")
                if 'group' in location:
                    location_group_map[location['group']].add(location['name'])
            locations_code.append("}\n")
            append_locations_code.append(f"    for location_name in {region_to_normalized_locations(region)}:")
            if region['name'] != "Abyss - Nonota":
                append_locations_code.append(f"        location_id = location_name_to_id[location_name]")
            else:
                append_locations_code.append(f"        if location_name != \"Abyss - Nonota\":")
                append_locations_code.append(f"            location_id = location_name_to_id[location_name]")
                append_locations_code.append(f"        else:")
                append_locations_code.append(f"            location_id = None")
            append_locations_code.append(f"        group_name = {region_to_normalized_locations(region)}[location_name]")
            append_locations_code.append(f"        region = world.multiworld.get_region(\"{region['name']}\", world.player)")
            append_locations_code.append(f"        add_location_to_region(location_name, location_id, group_name, region, world)\n")

        lwn_region = f"    \"{region['name']}\": "
        if 'exits' in region and region['exits']:
            lwn_region += "{"
            for region_exit in region['exits']:
                lwn_region += f"\"{region_exit['name']}\", "
                rule = region_exit['rules'] if isinstance(region_exit['rules'], str) else "True"
                if rule.find(" or ") >= 0 or rule.find(" and ") >= 0:
                    rule = "(" + rule + ")"
                subbed_rule = re.sub(' or ', r"\n                       or ", rule)
                subbed_rule = re.sub(' and ', r"\n                       and ", subbed_rule)
                rules_code.append(f"    multiworld.get_entrance(\"{region['name']} -> "
                                  f"{region_exit['name']}\", player).access_rule = \\\n"
                                  f"        lambda state: {subbed_rule}")
            lwn_region = lwn_region[:-2]
            lwn_region += "},"
        else:
            lwn_region += "set(),"
        lwn_regions.append(lwn_region)

    locations_code.append('\n'.join(lwn_locations))
    locations_code.append("}\n")

    locations_code.append("location_name_to_id: Dict[str, int] "
                          "= {name: base_id + index for index, name in enumerate(sorted(lwn_locations))}\n")

    for loc_group_name in location_group_map.keys():
        location_name_groups.append(f"    \"{loc_group_name}\": {{")
        for loc in sorted(location_group_map[loc_group_name]):
            location_name_groups.append(f"        \"{loc}\",")
        location_name_groups.append("    },")
    location_name_groups.append("}\n")

    locations_code.append(('\n'.join(location_name_groups)) + '\n')
    locations_code.append('\n'.join(append_locations_code))

    regions_code.append('\n'.join(lwn_regions))
    regions_code.append("}\n")

    rules_code.append("\n\ndef set_location_rules(world: \"LWNWorld\") -> None:")
    rules_code.append("    multiworld = world.multiworld")
    rules_code.append("    player = world.player")
    rules_code.append("    options = world.options\n")
    rules_code.append('\n'.join(location_rules))
    rules_code.append('')

    # Write to locations.py
    with open('locations.py', 'w') as file:
        file.write('\n'.join(locations_code))

    # Write to regions.py
    with open('regions.py', 'w') as file:
        file.write('\n'.join(regions_code))

    # Write to rules.py
    with open('rules.py', 'w') as file:
        file.write('\n'.join(rules_code))

    print("Files generated successfully.")


if __name__ == "__main__":
    path = str(sys.argv[1])
    json_to_ap_python(path)
