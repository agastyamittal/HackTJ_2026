import re
import json

COLOR_WORDS = {
    "black": "Black",
    "blue": "Blue",
    "brown": "Brown",
    "green": "Green",
    "gray": "Grey",
    "grey": "Grey",
    "orange": "Orange",
    "pink": "Pink",
    "purple": "Purple",
    "red": "Red",
    "white": "White",
    "yellow": "Yellow"
}

UPPER_GARMENTS = {
    "hoodie": "upperBodyOther",
    "tshirt": "upperBodyTshirt",
    "t-shirt": "upperBodyTshirt",
    "shirt": "upperBodyShirt",
    "jacket": "upperBodyOther",
    "coat": "upperBodyOther",
    "sweater": "upperBodyOther"
}

LOWER_GARMENTS = {
    "pants": "lowerBodyTrousers",
    "trousers": "lowerBodyTrousers",
    "jeans": "lowerBodyJeans",
    "shorts": "lowerBodyShorts",
    "skirt": "lowerBodyShortSkirt",
    "long skirt": "lowerBodyLongSkirt"
}

FOOTWEAR_TYPES = {
    "shoes": "footwearShoes",
    "shoe": "footwearShoes",
    "sneakers": "footwearSneakers",
    "sneaker": "footwearSneakers",
    "boots": "footwearBoots",
    "boot": "footwearBoots",
    "sandals": "footwearSandals",
    "sandal": "footwearSandals",
    "leather shoes": "footwearLeatherShoes"
}

CARRYING_TYPES = {
    "backpack": "carryingBackpack",
    "messenger bag": "carryingMessengerBag",
    "plastic bags": "carryingPlasticBags",
    "plastic bag": "carryingPlasticBags",
    "tote bag": "carryingToteBag",
    "luggage": "carryingLuggageCase",
    "luggage case": "carryingLuggageCase"
}

ACCESSORIES = {
    "hat": "accessoryHat",
    "sunglasses": "accessorySunglasses"
}

GENDERS = {
    "male": "personalMale",
    "man": "personalMale",
    "boy": "personalMale",
    "female": "personalFemale",
    "woman": "personalFemale",
    "girl": "personalFemale"
}

AGES = {
    "young": "personalLess30",
    "under 30": "personalLess30",
    "less than 30": "personalLess30",
    "under 45": "personalLess45",
    "middle aged": "personalLess45",
    "older": "personalLess60",
    "elderly": "personalLarger60"
}

HAIR_COLORS = {
    "black hair": "hairBlack",
    "brown hair": "hairBrown",
    "blonde hair": "hairBlond",
    "gray hair": "hairGrey",
    "grey hair": "hairGrey"
}

HAIR_LENGTH = {
    "short hair": "hairShort",
    "long hair": "hairLong"
}


def make_color_token(prefix: str, color: str):
    return f"{prefix}{COLOR_WORDS[color]}"


def parse_person_query(query: str):
    text = query.lower()
    attributes = []

    # upper body color + garment
    for garment_word, garment_token in UPPER_GARMENTS.items():
        pattern = rf"\b({'|'.join(COLOR_WORDS.keys())})\s+{re.escape(garment_word)}\b"
        match = re.search(pattern, text)
        if match:
            attributes.append(make_color_token("upperBody", match.group(1)))
            attributes.append(garment_token)
            break
    else:
        for garment_word, garment_token in UPPER_GARMENTS.items():
            if re.search(rf"\b{re.escape(garment_word)}\b", text):
                attributes.append(garment_token)
                break

    # lower body color + garment
    for garment_word, garment_token in sorted(LOWER_GARMENTS.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b({'|'.join(COLOR_WORDS.keys())})\s+{re.escape(garment_word)}\b"
        match = re.search(pattern, text)
        if match:
            attributes.append(make_color_token("lowerBody", match.group(1)))
            attributes.append(garment_token)
            break
    else:
        for garment_word, garment_token in sorted(LOWER_GARMENTS.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(garment_word)}\b", text):
                attributes.append(garment_token)
                break

    # footwear color + type
    for footwear_word, footwear_token in sorted(FOOTWEAR_TYPES.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b({'|'.join(COLOR_WORDS.keys())})\s+{re.escape(footwear_word)}\b"
        match = re.search(pattern, text)
        if match:
            attributes.append(make_color_token("footwear", match.group(1)))
            attributes.append(footwear_token)
            break
    else:
        for footwear_word, footwear_token in sorted(FOOTWEAR_TYPES.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(footwear_word)}\b", text):
                attributes.append(footwear_token)
                break

    # carrying
    for phrase, token in sorted(CARRYING_TYPES.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            attributes.append(token)
            break

    # accessory
    for word, token in ACCESSORIES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            attributes.append(token)
            break

    # gender
    for word, token in GENDERS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            attributes.append(token)
            break

    # age
    for phrase, token in AGES.items():
        if phrase in text:
            attributes.append(token)
            break

    # hair color
    for phrase, token in HAIR_COLORS.items():
        if phrase in text:
            attributes.append(token)
            break

    # hair length
    for phrase, token in HAIR_LENGTH.items():
        if phrase in text:
            attributes.append(token)
            break

    # defaults if not specified
    if not any(x.startswith("carrying") for x in attributes):
        attributes.append("carryingNothing")

    if not any(x.startswith("accessory") for x in attributes):
        attributes.append("accessoryNothing")

    return {
        "attributes": attributes
    }


if __name__ == "__main__":
    while True:
        q = input("Enter person query (or 'quit'): ").strip()
        if q.lower() == "quit":
            break

        parsed = parse_person_query(q)
        print(json.dumps(parsed, indent=2))
        print("-" * 40)