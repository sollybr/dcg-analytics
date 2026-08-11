from django.db import models

from analytics.models import DigimonCard


EXCLUDED_FIELDS = {
    "id",
    "data",
    "created_at",
    "updated_at",
}

# Fields that are stored as strings (CharField) but represent an ordinal/
# numeric concept. These must NOT also be classified as "categorical" by
# get_analytics_fields, or a field like card_level will silently answer to
# both get_categorical_fields() and get_numeric_like_fields() with no
# single source of truth for which one a caller should use.
NUMERIC_LIKE_FIELD_NAMES = {"card_level", "play_cost"}

FORCE_CATEGORICAL = ["subtype", "type", "color", "card_type"]


def get_analytics_fields(model=DigimonCard):
    fields = {}

    for field in model._meta.fields:
        if field.name in EXCLUDED_FIELDS:
            continue

        if field.name in NUMERIC_LIKE_FIELD_NAMES:
            fields[field.name] = {
                "name": field.name,
                "type": "numeric",
                "django_type": field.get_internal_type(),
                "source_type": "string",
            }

        elif isinstance(field, models.CharField) or field.name in FORCE_CATEGORICAL:
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
    return {
        name: field
        for name, field in get_analytics_fields(model).items()
        if field["type"] == "numeric"
    }