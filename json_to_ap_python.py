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
        "from typing import Dict, Set, Any, TYPE_CHECKING",
        "from BaseClasses import Location\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "class LWNLocation(Location):",
        "    game: str = \"Little Witch Nobeta\"\n",
        "    # override constructor to automatically mark event locations as such",
        "    def __init__(self, player: int, name=\"\", code=None, parent=None):",
        "        super(LWNLocation, self).__init__(player, name, code, parent)",
        "        self.event = code is None\n\n",
        "base_id = 345600000\n",
    ]

    lwn_locations = [
        "lwn_locations: Dict[str, Any] = {",
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
        "from .options import Toggle",
        "from worlds.generic.Rules import set_rule",
        "from BaseClasses import CollectionState\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "def has_fire_or_thunder(state: CollectionState, player: int) -> bool:",
        "    return state.has_any([\"Fire\", \"Thunder\"], player)\n\n",
        "def has_wind_or_skip(state: CollectionState, player: int, world: \"LWNWorld\") -> bool:",
        "    return (state.has(\"Wind\", player) or",
        "            world.options.wind_requirements.value == world.options.wind_requirements.option_less_wind_requirements)",
        "\n",
        "def has_wind_or_damage_boost(state: CollectionState, player: int, world: \"LWNWorld\") -> bool:",
        "    return (state.has(\"Wind\", player) or",
        "            (world.options.wind_requirements.value == world.options.wind_requirements.option_less_wind_requirements and ",
        "            state.has(\"Fire\", player)))\n\n",
        "def set_region_rules(world: \"LWNWorld\") -> None:",
        "    multiworld = world.multiworld",
        "    player = world.player",
        "    options = world.options",
    ]

    location_rules = []

    for region in data['regions']:
        if 'locations' in region and region['locations']:
            region_locations = region_to_normalized_locations(region)
            lwn_locations.append(f"    **dict.fromkeys({region_locations}, None),")
            region_locations += ": Set[str] = {"
            locations_code.append(f"{region_locations}")
            for location in region['locations']:
                if 'id' in location and 'name' in location:
                    locations_code.append(f"    \"{location['name']}\",")
                else:
                    locations_code.append(f"    \"{location['name']}\",")
                if 'rules' in location:
                    location_rules.append(f"    set_rule(multiworld.get_location(\"{location['name']}\", player),")
                    location_rules.append(f"             lambda state: {location['rules']})")
                if 'group' in location:
                    location_group_map[location['group']].add(location['name'])
            locations_code.append("}\n")
            append_locations_code.append(f"    for location_name in {region_to_normalized_locations(region)}:")
            append_locations_code.append(f"        location_id = location_name_to_id[location_name]")
            append_locations_code.append(f"        region = world.multiworld.get_region(\"{region['name']}\", world.player)")
            append_locations_code.append(f"        region.locations.append(LWNLocation("
                                         f"world.player, location_name, location_id, region))\n")

        lwn_region = f"    \"{region['name']}\": "
        if 'exits' in region and region['exits']:
            lwn_region += "{"
            for region_exit in region['exits']:
                lwn_region += f"\"{region_exit['name']}\", "
                rule = region_exit['rules'] if isinstance(region_exit['rules'], str) else "True"
                rules_code.append(f"    multiworld.get_entrance(\"{region['name']} -> "
                                  f"{region_exit['name']}\", player).access_rule = \\\n"
                                  f"        lambda state: {rule}")
            lwn_region = lwn_region[:-2]
            lwn_region += "},"
        else:
            lwn_region += "set(),"
        lwn_regions.append(lwn_region)

    locations_code.append('\n'.join(lwn_locations))
    locations_code.append("}\n")

    locations_code.append("location_name_to_id: Dict[str, int] "
                          "= {name: base_id + index for index, name in enumerate(lwn_locations)}\n")

    for loc_group_name in location_group_map.keys():
        location_name_groups.append(f"    \"{loc_group_name}\": {{")
        for loc in sorted(location_group_map[loc_group_name]):
            location_name_groups.append(f"        \"{loc}\",")
        location_name_groups.append("    },")
    location_name_groups.append("}\n")

    locations_code.append(('\n'.join(location_name_groups)).__add__('\n'))
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
