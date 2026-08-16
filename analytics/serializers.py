from rest_framework import serializers
from .models import DigimonCard, CardImage


class CardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardImage
        fields = ['id', 'image_url', 'variant_type', 'is_primary', 'source_filename']


class CardSerializer(serializers.ModelSerializer):
    images = CardImageSerializer(many=True, read_only=True)

    class Meta:
        model = DigimonCard
        fields = ['id', 'card_number', 'name', 'card_type', 'color', 'images']
from rest_framework import serializers
from .models import DigimonCard, CardExpansion

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

    def get_expansion_name(self, obj: DigimonCard) -> str:
        if not obj.expansion:
            return "Unknown Expansion"

        # 1. Direct match on exact code (e.g., BT18-19)
        exp = CardExpansion.objects.filter(expansion_code=obj.expansion).first()
        if exp and exp.expansion_name:
            return exp.expansion_name

        # 2. Range containment match if card has base code like 'BT19'
        range_exp = CardExpansion.objects.filter(
            expansion_code__icontains=obj.expansion
        ).first()
        if range_exp and range_exp.expansion_name:
            return range_exp.expansion_name

        return obj.expansion