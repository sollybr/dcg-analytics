from statistics import mean, median, stdev


def clean_numeric_values(values):
    cleaned = []

    for value in values:
        try:
            cleaned.append(float(value))
        except (TypeError, ValueError):
            continue

    return cleaned


def descriptive_statistics(values):
    values = clean_numeric_values(values)

    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "standard_deviation": None,
        }

    result = {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
        "standard_deviation": (
            stdev(values)
            if len(values) > 1
            else 0
        ),
    }

    return result