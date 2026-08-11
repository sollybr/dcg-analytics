from collections import Counter


def _tokenize(queryset):
    """Count values from a flat queryset, splitting multi-value fields on '/'."""
    counter = Counter()

    for raw_val in queryset:
        if not raw_val or raw_val == "-":
            continue

        for val in raw_val.split("/"):
            cleaned = val.strip()
            if cleaned and cleaned != "-":
                counter[cleaned] += 1

    return counter


def _build_distribution(counter, baseline_counter=None, baseline_total=None):
    total = sum(counter.values())
    results = []

    for val, count in counter.most_common():
        percentage = (count / total) if total else 0

        entry = {
            "value": val,
            "count": count,
            "percentage": percentage,
        }

        if baseline_counter is not None and baseline_total:
            baseline_count = baseline_counter.get(val, 0)
            baseline_percentage = baseline_count / baseline_total
            entry["baseline_percentage"] = baseline_percentage
            # lift > 1 means over-represented vs the full card pool, < 1 under-represented
            entry["lift"] = (
                percentage / baseline_percentage if baseline_percentage else None
            )

        results.append(entry)

    return results, total


def conditional_distribution(
    model,
    given_field,
    target_field,
    given_value,
    include_baseline=True,
):
    if given_field in ["subtype", "color", "card_type", "type"]:
        filters = {f"{given_field}__icontains": given_value}
    else:
        filters = {f"{given_field}__iexact": given_value}

    queryset = model.objects.filter(**filters).values_list(target_field, flat=True)
    counter = _tokenize(queryset)

    baseline_counter = None
    baseline_total = None
    if include_baseline:
        full_queryset = model.objects.values_list(target_field, flat=True)
        baseline_counter = _tokenize(full_queryset)
        baseline_total = sum(baseline_counter.values())

    distribution, total = _build_distribution(counter, baseline_counter, baseline_total)

    return {
        "given": {"field": given_field, "value": given_value},
        "target": {"field": target_field},
        "sample_size": total,
        "baseline_sample_size": baseline_total,
        "distribution": distribution,
    }