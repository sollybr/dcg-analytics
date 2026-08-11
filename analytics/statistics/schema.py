from django.db import models

from analytics.models import DigimonCard


EXCLUDED_FIELDS = {
    "id",
    "data",
    "created_at",
    "updated_at",
}


def get_analytics_fields(model=DigimonCard):
    fields = {}

    FORCE_CATEGORICAL = ["subtype", "type", "color", "card_type"] 

    for field in model._meta.fields:
        if field.name in EXCLUDED_FIELDS:
            continue

        if isinstance(field, models.CharField) or field.name in FORCE_CATEGORICAL:
            fields[field.name] = {
                "name": field.name,
                "type": "categorical",
                "django_type": field.get_internal_type(),
            }

        elif isinstance(field, models.TextField):
            fields[field.name] = {
                "name": field.name,
                "type": "text",
                "django_type": field.get_internal_type(),
            }

    return fields


def get_categorical_fields(model=DigimonCard):
    return {
        name: field
        for name, field in get_analytics_fields(model).items()
        if field["type"] == "categorical"
    }


def get_numeric_like_fields(model=DigimonCard):
    numeric_like = {}

    for name in get_analytics_fields(model):
        if name in {"card_level", "play_cost"}:
            numeric_like[name] = {
                "name": name,
                "type": "numeric",
                "source_type": "string",
            }

    return numeric_like