"""
Natural language query parser for feature-based camera scoring.
Ported from DataSet/PETA/test_extract.py and DataSet/VeRi/test_extract_vehicle.py.

parse_query(text) -> list[str]  — returns attribute tokens from the query
"""

import re

# ── Person attribute mappings ──────────────────────────────────────────────────

_COLOR_WORDS = {
    "black": "Black", "blue": "Blue", "brown": "Brown", "green": "Green",
    "gray": "Grey",   "grey": "Grey", "orange": "Orange", "pink": "Pink",
    "purple": "Purple", "red": "Red", "white": "White", "yellow": "Yellow",
}

_UPPER_GARMENTS = {
    "hoodie":   "upperBodyHoodie",
    "tshirt":   "upperBodyTshirt",
    "t-shirt":  "upperBodyTshirt",
    "shirt":    "upperBodyTshirt",
    "jacket":   "upperBodyJacket",
    "coat":     "upperBodyJacket",
    "sweater":  "upperBodyJacket",
}

_LOWER_GARMENTS = {
    "pants":      "lowerBodyTrousers",
    "trousers":   "lowerBodyTrousers",
    "jeans":      "lowerBodyJeans",
    "shorts":     "lowerBodyShorts",
    "long skirt": "lowerBodySkirt",
    "skirt":      "lowerBodySkirt",
}

_CARRYING_TYPES = {
    "messenger bag": "carryingMessengerBag",
    "backpack":      "carryingBackpack",
    "bag":           "carryingBag",
}

_GENDERS = {
    "male": "personalMale", "man": "personalMale", "boy": "personalMale",
    "female": "personalFemale", "woman": "personalFemale", "girl": "personalFemale",
}

_SLEEVE_LENGTHS = {
    "long sleeve":   "upperBodyLongSleeve",
    "long-sleeve":   "upperBodyLongSleeve",
    "long sleeved":  "upperBodyLongSleeve",
    "long sleeves":  "upperBodyLongSleeve",
    "short sleeve":  "upperBodyShortSleeve",
    "short-sleeve":  "upperBodyShortSleeve",
    "short sleeved": "upperBodyShortSleeve",
    "short sleeves": "upperBodyShortSleeve",
}

_STYLES = {
    "casual":      "upperBodyCasual",
    "formal":      "upperBodyFormal",
    "dress shirt": "upperBodyFormal",
    "suit":        "upperBodyFormal",
}

# ── Vehicle attribute mappings ─────────────────────────────────────────────────

_VEHICLE_COLOR_WORDS = {
    "yellow": "Yellow", "orange": "Orange", "green": "Green", "gray": "Gray",
    "grey":   "Gray",   "red":    "Red",    "blue":  "Blue",  "white": "White",
    "golden": "Golden", "brown":  "Brown",  "black": "Black",
}

_VEHICLE_TYPES = {
    "sedan":    "Sedan",    "suv":     "SUV",    "van":    "Van",
    "hatchback":"Hatchback","mpv":     "MPV",    "pickup": "Pickup",
    "bus":      "Bus",      "truck":   "Truck",  "estate": "Estate",
}

_VEHICLE_KEYWORDS = set(_VEHICLE_TYPES.keys()) | {"car", "vehicle"}

# Maps classifier output (lowercase) → query token — used by detector.py
VEHICLE_COLOR_TO_TOKEN = {c: f"color{cap}" for c, cap in _VEHICLE_COLOR_WORDS.items()}
VEHICLE_TYPE_TO_TOKEN  = {t: f"type{cap}"  for t, cap in _VEHICLE_TYPES.items()}

# Attributes the classifier can actually detect — used to bound the denominator
DETECTABLE_PERSON_ATTRS = {
    "upperBodyBlue", "upperBodyRed", "upperBodyBlack", "upperBodyWhite", "upperBodyGreen",
    "upperBodyLongSleeve", "upperBodyShortSleeve",
    "upperBodyCasual", "upperBodyFormal",
    "upperBodyTshirt", "upperBodyHoodie", "upperBodyJacket",
    "lowerBodyJeans", "lowerBodyTrousers", "lowerBodyShorts", "lowerBodySkirt",
    "carryingBackpack", "carryingBag", "carryingMessengerBag",
    "personalMale", "personalFemale",
}
DETECTABLE_VEHICLE_ATTRS = set(VEHICLE_COLOR_TO_TOKEN.values()) | set(VEHICLE_TYPE_TO_TOKEN.values())
DETECTABLE_ATTRS = DETECTABLE_PERSON_ATTRS | DETECTABLE_VEHICLE_ATTRS


# ── Parsers ────────────────────────────────────────────────────────────────────

def parse_person_query(query: str) -> list[str]:
    text = query.lower()
    attrs = []

    # upper body: color + garment
    for garment, token in _UPPER_GARMENTS.items():
        pat = rf"\b({'|'.join(_COLOR_WORDS.keys())})\s+{re.escape(garment)}\b"
        m = re.search(pat, text)
        if m:
            attrs.append(f"upperBody{_COLOR_WORDS[m.group(1)]}")
            attrs.append(token)
            break
    else:
        for garment, token in _UPPER_GARMENTS.items():
            if re.search(rf"\b{re.escape(garment)}\b", text):
                attrs.append(token)
                break

    # upper body: standalone color (e.g. "red hoodie" already handled, but "wearing red")
    if not any(a.startswith("upperBody") and a[9:9+3] not in ("Lon", "Sho", "Cas", "For", "Tsh", "Hoo", "Jac") for a in attrs):
        for color, cap in _COLOR_WORDS.items():
            if re.search(rf"\b{re.escape(color)}\b", text):
                attrs.append(f"upperBody{cap}")
                break

    # lower body: color + garment
    for garment, token in sorted(_LOWER_GARMENTS.items(), key=lambda x: -len(x[0])):
        pat = rf"\b({'|'.join(_COLOR_WORDS.keys())})\s+{re.escape(garment)}\b"
        m = re.search(pat, text)
        if m:
            attrs.append(f"lowerBody{_COLOR_WORDS[m.group(1)]}")
            attrs.append(token)
            break
    else:
        for garment, token in sorted(_LOWER_GARMENTS.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(garment)}\b", text):
                attrs.append(token)
                break

    # carrying
    for phrase, token in sorted(_CARRYING_TYPES.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            attrs.append(token)
            break

    # gender
    for word, token in _GENDERS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            attrs.append(token)
            break

    # sleeve length
    for phrase, token in sorted(_SLEEVE_LENGTHS.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            attrs.append(token)
            break

    # style
    for phrase, token in sorted(_STYLES.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            attrs.append(token)
            break

    return attrs


def parse_vehicle_query(query: str) -> list[str]:
    text = query.lower()
    attrs = []

    found_type = False
    for vtype, cap in _VEHICLE_TYPES.items():
        pat = rf"\b({'|'.join(_VEHICLE_COLOR_WORDS.keys())})\s+{re.escape(vtype)}\b"
        m = re.search(pat, text)
        if m:
            attrs.append(f"color{_VEHICLE_COLOR_WORDS[m.group(1)]}")
            attrs.append(f"type{cap}")
            found_type = True
            break

    if not found_type:
        for vtype, cap in _VEHICLE_TYPES.items():
            if re.search(rf"\b{re.escape(vtype)}\b", text):
                attrs.append(f"type{cap}")
                found_type = True
                break

    found_color = any(a.startswith("color") for a in attrs)
    if not found_color:
        for generic in ["car", "vehicle"]:
            pat = rf"\b({'|'.join(_VEHICLE_COLOR_WORDS.keys())})\s+{re.escape(generic)}\b"
            m = re.search(pat, text)
            if m:
                attrs.append(f"color{_VEHICLE_COLOR_WORDS[m.group(1)]}")
                found_color = True
                break

    return attrs


def parse_query(query: str) -> list[str]:
    """
    Parse a natural language query into attribute tokens.
    Runs person parser always; vehicle parser only if vehicle keywords are present.
    Filters to only detectable attributes (ones the classifier can produce).
    Returns deduplicated list.
    """
    text = query.lower()
    features = parse_person_query(query)

    if any(kw in text.split() or kw in text for kw in _VEHICLE_KEYWORDS):
        features += parse_vehicle_query(query)

    # Deduplicate and keep only what the classifier can actually detect
    seen = set()
    result = []
    for f in features:
        if f not in seen and f in DETECTABLE_ATTRS:
            seen.add(f)
            result.append(f)

    return result
