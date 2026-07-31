import json
import requests
from collections import Counter
from django.core.cache import cache
from django.shortcuts import render

DATA_URL = "https://raw.githubusercontent.com/TakaOtaku/Digimon-Card-App/main/src/assets/cardlists/DigimonCards.json"
CACHE_TIMEOUT = 60 * 60 * 6  # Cache for 6 hours

def is_released(card):
    """
    Determines if a card is officially released by checking restriction flags,
    placeholder names, and missing rarity markers.
    """
    # 1. Check restrictions dictionary for "Not released"
    restrictions = card.get('restrictions', {})
    if isinstance(restrictions, dict):
        if restrictions.get('english') == 'Not released':
            return False

    # 2. Check for placeholder wiki/category names
    name_obj = card.get('name', {})
    eng_name = name_obj.get('english', '') if isinstance(name_obj, dict) else str(name_obj)
    if not eng_name or eng_name.startswith('[[:Category:') or eng_name == '-':
        return False

    # 3. Check for placeholder rarity or missing card numbers
    rarity = str(card.get('rarity', '')).strip()
    if rarity == '-' or not rarity:
        return False

    return True

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
    
    # Filter out unreleased and placeholder cards
    released_cards = [card for card in raw_cards if is_released(card)]

    type_counter = Counter()
    name_counter = Counter()
    color_counter = Counter()
    expansion_counter = Counter()
    sec_color_counter = Counter()

    for card in released_cards:
        # 1. Card Type Distribution
        card_type = card.get('cardType', 'Unknown')
        type_counter[card_type] += 1

        # 2. Number of Cards per Name (English name)
        name_obj = card.get('name')
        if isinstance(name_obj, dict):
            english_name = name_obj.get('english', 'Unknown')
        else:
            english_name = str(name_obj) if name_obj else 'Unknown'
        name_counter[english_name] += 1

        # 3. Color Distribution
        color = card.get('color', 'Unknown')
        color_counter[color] += 1

        # 4. Cards per Expansion Set
        card_number = card.get('cardNumber', '')
        notes = card.get('notes', '')
        
        if '-' in card_number:
            set_code = card_number.split('-')[0].strip()
        elif notes and ':' in notes:
            set_code = notes.split(':')[0].strip()
        else:
            set_code = 'Other'
            
        expansion_counter[set_code] += 1

        # 5. Color by Secret Rarity (Rarity == 'SEC')
        rarity = str(card.get('rarity', '')).upper()
        if 'SEC' in rarity:
            sec_color_counter[color] += 1

    # Top 15 most printed card names
    top_names = name_counter.most_common(15)

    # Sort expansion sets alphabetically
    sorted_expansions = sorted(expansion_counter.items(), key=lambda x: x[0])

    context = {
        'total_cards': len(released_cards),
        
        # 1. Card Type
        'type_labels': json.dumps(list(type_counter.keys())),
        'type_data': json.dumps(list(type_counter.values())),

        # 2. Most Common Names (Top 15)
        'name_labels': json.dumps([x[0] for x in top_names]),
        'name_data': json.dumps([x[1] for x in top_names]),

        # 3. Color Distribution
        'color_labels': json.dumps(list(color_counter.keys())),
        'color_data': json.dumps(list(color_counter.values())),

        # 4. Expansion Sets
        'expansion_labels': json.dumps([x[0] for x in sorted_expansions]),
        'expansion_data': json.dumps([x[1] for x in sorted_expansions]),

        # 5. Secret Rare Colors
        'sec_color_labels': json.dumps(list(sec_color_counter.keys())),
        'sec_color_data': json.dumps(list(sec_color_counter.values())),
    }
    
    return render(request, 'dashboard.html', context)