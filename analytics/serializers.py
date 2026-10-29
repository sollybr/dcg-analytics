from rest_framework import serializers

from .models import CardImage, DigimonCard
from .utils.expansions import get_expansion_map, resolve_expansion_name


class CardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardImage
        fields = ['id', 'image_url', 'variant_type', 'is_primary', 'source_filename']


class CardSerializer(serializers.ModelSerializer):
    images = CardImageSerializer(many=True, read_only=True)

    class Meta:
        model = DigimonCard
        fields = ['id', 'card_number', 'name', 'card_type', 'color', 'images']


class DigimonCardSerializer(serializers.ModelSerializer):
    expansion_name = serializers.SerializerMethodField()

    class Meta:
        model = DigimonCard
        fields = [
            'id',
            'card_number',
            'name',
            'expansion',        # e.g., "BT18-19" or "BT19"
            'expansion_name',   # e.g., "SPECIAL BOOSTER VER.2.0 [BT18-19]"
            # ... other fields
        ]

    def _expansion_map(self) -> dict:
        # Load {code: name} once per request and share it across every card
        # in a list response (child serializers share the root's context).
        context = self.context
        if "expansion_map" not in context:
            context["expansion_map"] = get_expansion_map()
        return context["expansion_map"]

    def get_expansion_name(self, obj: DigimonCard) -> str:
        return resolve_expansion_name(obj.expansion, self._expansion_map())
