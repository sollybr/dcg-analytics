from django.db import models


class DigimonCard(models.Model):
    card_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
    )
    rarity = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )
    card_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )
    color = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )
    card_level = models.CharField(
        max_length=32,
        blank=True,
        default="",
    )
    play_cost = models.CharField(
        max_length=32,
        blank=True,
        default="",
    )
    expansion = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )
    subtype = models.TextField(
        blank=True,
        default="",
    )

    data = models.JSONField(
        default=dict,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["card_number"]

    def __str__(self):
        return f"{self.card_number} - {self.name}"

    @property
    def primary_image_url(self):
        """Helper to retrieve primary standard image URL."""
        primary = self.images.filter(is_primary=True).first()
        return primary.image_url if primary else None


class CardImage(models.Model):
    VARIANT_CHOICES = [
        ('standard', 'Standard Art'),
        ('alternate_art', 'Alternate Art (Parallel Rare)'),
        ('promo', 'Promo Variant'),
        ('errata', 'Text Correction / Errata'),
    ]

    card = models.ForeignKey(
        DigimonCard,  # Updated FK to reference DigimonCard
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.URLField(max_length=500)
    variant_type = models.CharField(max_length=30, choices=VARIANT_CHOICES, default='standard')
    is_primary = models.BooleanField(default=False)
    source_filename = models.CharField(max_length=255)
    storage_backend = models.CharField(max_length=50, default='vercel_blob')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['card', 'source_filename'],
                name='unique_card_image_source'
            )
        ]

    def __str__(self):
        return f"{self.card.card_number} - {self.variant_type} ({self.source_filename})"
