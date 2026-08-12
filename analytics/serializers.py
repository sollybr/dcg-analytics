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