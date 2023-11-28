import re
import json


def convert_header_to_json(header_file_path, json_file_path):
    # Regular expression to match C macro definitions
    macro_pattern = re.compile(r"#define\s+(\w+)\s+([0-9xXA-Fa-f]+)")

    with open(header_file_path, 'r') as file:
        content = file.read()

    # Find all macro definitions
    macros = macro_pattern.findall(content)

    # Convert macros to JSON format
    json_data = {"Protocol_1": {"Control_Table": {}}}

    for name, value in macros:
        bytelen = 1

        # Convert hexadecimal values to integers
        value = str(value)
        value = value.lower()
        if value.startswith('0x') and len(value) <= 4:
            value = int(value, 16)
        elif len(value) <= 4:
            value = int(value)
        else:
            value = value.upper()

        # Check if suffix is L
        if name.endswith('L'):
            name = name[:-2]
            bytelen = 2

        if not name.endswith('H'):
            # Add to JSON structure
            json_data["Protocol_1"]["Control_Table"][name] = [value, bytelen]

    # Write the JSON data to a file
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=2)


# Example usage
header_file = '../3mxlControlTable.h'
json_file = '../dynio/DynamixelJSON/3mxl.json'
convert_header_to_json(header_file, json_file)
