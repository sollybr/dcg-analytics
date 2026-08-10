from django.db.models import Count


def conditional_distribution(
    model,
    given_field,
    target_field,
    given_value,
):
    filters = {
        f"{given_field}__iexact": given_value,
    }

    queryset = (
        model.objects
        .filter(**filters)
        .values(target_field)
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    rows = [
        row
        for row in queryset
        if row[target_field] not in (None, "")
    ]

    total = sum(
        row["count"]
        for row in rows
    )

    return [
        {
            "value": row[target_field],
            "count": row["count"],
            "percentage": (
                row["count"] / total
                if total
                else 0
            ),
        }
        for row in rows
    ]