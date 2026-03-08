import re
import json

COLOR_WORDS = {
    "yellow": "Yellow",
    "orange": "Orange",
    "green": "Green",
    "gray": "Gray",
    "grey": "Gray",
    "red": "Red",
    "blue": "Blue",
    "white": "White",
    "golden": "Golden",
    "brown": "Brown",
    "black": "Black"
}

VEHICLE_TYPES = {
    "sedan": "Sedan",
    "suv": "SUV",
    "van": "Van",
    "hatchback": "Hatchback",
    "mpv": "MPV",
    "pickup": "Pickup",
    "bus": "Bus",
    "truck": "Truck",
    "estate": "Estate"
}

GENERAL_VEHICLE_WORDS = [
    "car",
    "vehicle"
]

def make_color_token(color: str):
    return f"color{COLOR_WORDS[color]}"

def make_type_token(vehicle_type: str):
    return f"type{VEHICLE_TYPES[vehicle_type]}"

def parse_vehicle_query(query: str):
    text = query.lower()
    attributes = []

    # color + exact type, like "black suv"
    found_type = False
    for vehicle_word in VEHICLE_TYPES:
        pattern = rf"\b({'|'.join(COLOR_WORDS.keys())})\s+{re.escape(vehicle_word)}\b"
        match = re.search(pattern, text)
        if match:
            attributes.append(make_color_token(match.group(1)))
            attributes.append(make_type_token(vehicle_word))
            found_type = True
            break

    # type only
    if not found_type:
        for vehicle_word in VEHICLE_TYPES:
            if re.search(rf"\b{re.escape(vehicle_word)}\b", text):
                attributes.append(make_type_token(vehicle_word))
                found_type = True
                break

    # color + generic vehicle word, like "white car"
    found_color = any(attr.startswith("color") for attr in attributes)
    if not found_color:
        for generic_word in GENERAL_VEHICLE_WORDS:
            pattern = rf"\b({'|'.join(COLOR_WORDS.keys())})\s+{re.escape(generic_word)}\b"
            match = re.search(pattern, text)
            if match:
                attributes.append(make_color_token(match.group(1)))
                found_color = True
                break

    # fallback: any color anywhere
    if not found_color:
        for color_word in COLOR_WORDS:
            if re.search(rf"\b{re.escape(color_word)}\b", text):
                attributes.append(make_color_token(color_word))
                break

    return {
        "attributes": attributes
    }


if __name__ == "__main__":
    while True:
        q = input("Enter vehicle query (or 'quit'): ").strip()
        if q.lower() == "quit":
            break

        parsed = parse_vehicle_query(q)
        print(json.dumps(parsed, indent=2))
        print("-" * 40)