from django.db import models

class CardExpansion(models.Model):
    expansion_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )
    expansion_code = models.CharField(
        max_length=32,
        blank=True,
        default="",
        db_index=True,
    )

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

    # Stores the raw JSON payload from GitHub
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