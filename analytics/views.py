import requests
from collections import Counter
from django.core.cache import cache
from django.http import JsonResponse

DATA_URL = "https://raw.githubusercontent.com/TakaOtaku/Digimon-Card-App/main/src/assets/cardlists/DigimonCards.json"
CACHE_TIMEOUT = 60 * 60 * 6

def is_valid_card(card):
    name_obj = card.get('name', {})
    eng_name = name_obj.get('english', '') if isinstance(name_obj, dict) else str(name_obj)
    eng_name = str(eng_name).strip()
    if not eng_name or eng_name.startswith('[[:Category:') or eng_name == '-':
        return False

    rarity = str(card.get('rarity', '')).strip()
    if rarity == '-' or not rarity:
        return False

    card_number = str(card.get('cardNumber', '')).strip()
    if not card_number or card_number == '-':
        return False

    return True

def sanitize_card_text(card):
    text_fields = ["effect", "digivolveEffect", "securityEffect", "aceEffect", "specialDigivolve", "assembly"]
    for field in text_fields:
        val = card.get(field)
        if isinstance(val, str):
            card[field] = (
                val.replace('\u00a0', ' ')
                   .replace('\uff1c', '<')
                   .replace('\uff1e', '>')
            )
    return card

def fetch_digimon_data():
    data = cache.get("digimon_card_data")
    if not data:
        try:
            response = requests.get(DATA_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cache.set("digimon_card_data", data, CACHE_TIMEOUT)
        except Exception:
            data = []
    return data or []

def analytics_data(request):
    raw_cards = fetch_digimon_data()
    valid_cards = [
        sanitize_card_text(card) 
        for card in raw_cards 
        if is_valid_card(card)
    ]

    type_counter = Counter()
    name_counter = Counter()
    single_color_counter = Counter()
    multicolor_counter = Counter()
    expansion_counter = Counter()
    sec_color_counter = Counter()
    subtype_counter = Counter()

    for card in valid_cards:
        card_type = card.get('cardType', 'Unknown')
        if card_type and card_type != '-':
            type_counter[card_type] += 1

        name_obj = card.get('name')
        english_name = name_obj.get('english', 'Unknown') if isinstance(name_obj, dict) else (str(name_obj) if name_obj else 'Unknown')
        name_counter[english_name] += 1

        color = card.get('color', 'Unknown')
        if '/' in color:
            multicolor_counter[color] += 1
        else:
            single_color_counter[color] += 1

        card_number = card.get('cardNumber', '')
        notes = card.get('notes', '')
        if '-' in card_number:
            set_code = card_number.split('-')[0].strip()
        elif notes and ':' in notes:
            set_code = notes.split(':')[0].strip()
        else:
            set_code = 'Other'
        expansion_counter[set_code] += 1

        rarity = str(card.get('rarity', '')).upper()
        if 'SEC' in rarity:
            if '/' in color:
                for c in color.split('/'):
                    c_clean = c.strip()
                    if c_clean:
                        sec_color_counter[c_clean] += 1
            else:
                sec_color_counter[color] += 1

        raw_subtype = card.get('type', '') or card.get('types', '')
        if isinstance(raw_subtype, str) and raw_subtype:
            subtypes = [t.strip() for t in raw_subtype.split('/') if t.strip() and t.strip() != '-']
            for st in subtypes:
                subtype_counter[st] += 1

    top_names = name_counter.most_common(15)
    sorted_expansions = sorted(expansion_counter.items(), key=lambda x: x[0])
    top_multicolors = multicolor_counter.most_common(10)
    top_subtypes = subtype_counter.most_common(20)

    data = {
        'total_cards': len(valid_cards),
        'type_labels': list(type_counter.keys()),
        'type_data': list(type_counter.values()),
        'name_labels': [x[0] for x in top_names],
        'name_data': [x[1] for x in top_names],
        'single_color_labels': list(single_color_counter.keys()),
        'single_color_data': list(single_color_counter.values()),
        'multicolor_labels': [x[0] for x in top_multicolors],
        'multicolor_data': [x[1] for x in top_multicolors],
        'expansion_labels': [x[0] for x in sorted_expansions],
        'expansion_data': [x[1] for x in sorted_expansions],
        'sec_color_labels': list(sec_color_counter.keys()),
        'sec_color_data': list(sec_color_counter.values()),
        'subtype_labels': [x[0] for x in top_subtypes],
        'subtype_data': [x[1] for x in top_subtypes],
    }
    
    return JsonResponse(data)