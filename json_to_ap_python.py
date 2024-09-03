import sys
import json
import re


def json_to_ap_python(file_path):
    # Load the JSON data
    with open(file_path, 'r') as file:
        data = json.loads(file.read())

    # Generate locations.py
    locations_code = [
        "from typing import Dict\n",
        "base_id = 345600000\n"
    ]

    lwn_locations = [
        "lwn_locations: Dict[str, int] = {",
    ]

    # Generate regions.py
    regions_code = [
        "from typing import Dict, Set\n"
        "from BaseClasses import Region\n\n\n"
        "class LWNRegion(Region):\n"
        "    game: str = \"Little Witch Nobeta\"\n\n"
    ]

    lwn_regions = [
        "lwn_regions: Dict[str, Set[str]] = {"
    ]

    # Generate rules.py
    rules_code = [
        "from typing import TYPE_CHECKING\n",
        "from .options import LWNOptions, Toggle",
        "from worlds.generic.Rules import set_rule",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n\n"
        "def set_region_rules(world: \"LWNWorld\") -> None:\n"
        "    multiworld = world.multiworld\n"
        "    player = world.player\n"
        "    options = world.options\n"
    ]

    location_rules = []

    for region in data['regions']:
        if 'locations' in region and region['locations']:
            region_locations = re.sub(r'_+', '_', region['name'].replace(' ', '_').replace('-', '_')
                                      .replace('.', '').lower() + "_locations")
            lwn_locations.append(f"    **{region_locations},")
            region_locations += ": Dict[str, int] = {"
            locations_code.append(f"{region_locations}")
            for location in region['locations']:
                if 'id' in location and 'name' in location:
                    locations_code.append(f"    \"{location['name']}\": base_id + {location['id']},")
                else:
                    locations_code.append(f"    \"{location['name']}\": None,")
                if 'rules' in location:
                    location_rules.append(f"    set_rule(multiworld.get_location(\"{location['name']}\", player),")
                    location_rules.append(f"             lambda state: {location['rules']})")
            locations_code.append("}\n")

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
