from collections import Counter

def conditional_distribution(
    model,
    given_field,
    target_field,
    given_value,
):
    if given_field in ["subtype", "color", "card_type", "type"]:
        filters = {f"{given_field}__icontains": given_value}
    else:
        filters = {f"{given_field}__iexact": given_value}

    queryset = model.objects.filter(**filters).values_list(target_field, flat=True)

    counter = Counter()
    
    for raw_val in queryset:
        if not raw_val or raw_val == "-":
            continue
            
        # Split by '/' to handle multi-value fields (subtypes, colors, types)
        for val in raw_val.split("/"):
            cleaned = val.strip()
            if cleaned and cleaned != "-":
                counter[cleaned] += 1

    total = sum(counter.values())
    top_results = counter.most_common()

    return [
        {
            "value": val,
            "count": count,
            "percentage": (count / total) if total else 0,
        }
        for val, count in top_results
    ]