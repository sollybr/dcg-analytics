"""Card -> JSON serialization shared by the card-listing endpoints."""
from .expansions import get_expansion_map, resolve_expansion_name


def serialize_card(card, expansion_map):
    return {
        **card.data,
        "expansion": card.expansion,
        "expansion_name": resolve_expansion_name(card.expansion, expansion_map),
        "images": [
            {
                "image_url": img.image_url,
                "variant_type": img.variant_type,
                "is_primary": img.is_primary,
            }
            for img in card.images.all()
        ],
    }


def serialize_cards(cards):
    """Serialize an iterable of cards with a single expansion-name lookup."""
    expansion_map = get_expansion_map()
    return [serialize_card(card, expansion_map) for card in cards]
