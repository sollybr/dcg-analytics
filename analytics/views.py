import json
import requests
from collections import Counter
from django.core.cache import cache
from django.shortcuts import render

DATA_URL = "https://raw.githubusercontent.com/TakaOtaku/Digimon-Card-App/main/src/assets/cardlists/DigimonCards.json"
CACHE_TIMEOUT = 60 * 60 * 6  # Cache data for 6 hours

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

def dashboard(request):
    raw_cards = fetch_digimon_data()

    valid_cards = [
        sanitize_card_text(card) 
        for card in raw_cards 
        if is_valid_card(card)
    ]

    type_counter = Counter()
    name_counter = Counter()
    color_counter = Counter()
    expansion_counter = Counter()
    sec_color_counter = Counter()

    for card in valid_cards:

        card_type = card.get('cardType', 'Unknown')
        type_counter[card_type] += 1

        name_obj = card.get('name')
        if isinstance(name_obj, dict):
            english_name = name_obj.get('english', 'Unknown')
        else:
            english_name = str(name_obj) if name_obj else 'Unknown'
        name_counter[english_name] += 1

        color = card.get('color', 'Unknown')
        color_counter[color] += 1

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
            sec_color_counter[color] += 1

    top_names = name_counter.most_common(15)

    sorted_expansions = sorted(expansion_counter.items(), key=lambda x: x[0])

    context = {
        'total_cards': len(valid_cards),
        
        'type_labels': json.dumps(list(type_counter.keys())),
        'type_data': json.dumps(list(type_counter.values())),

        'name_labels': json.dumps([x[0] for x in top_names]),
        'name_data': json.dumps([x[1] for x in top_names]),

        'color_labels': json.dumps(list(color_counter.keys())),
        'color_data': json.dumps(list(color_counter.values())),

        'expansion_labels': json.dumps([x[0] for x in sorted_expansions]),
        'expansion_data': json.dumps([x[1] for x in sorted_expansions]),

        'sec_color_labels': json.dumps(list(sec_color_counter.keys())),
        'sec_color_data': json.dumps(list(sec_color_counter.values())),
    }
    
    return render(request, 'dashboard.html', context)