from statistics import mean


def rank_values(values):
    sorted_values = sorted(
        enumerate(values),
        key=lambda item: item[1],
    )

    ranks = [0] * len(values)

    for rank, (index, _) in enumerate(sorted_values, start=1):
        ranks[index] = rank

    return ranks


def spearman_correlation(first_values, second_values):
    if len(first_values) != len(second_values):
        raise ValueError("Value lists must have equal length.")

    if len(first_values) < 2:
        return None

    first_ranks = rank_values(first_values)
    second_ranks = rank_values(second_values)

    first_mean = mean(first_ranks)
    second_mean = mean(second_ranks)

    numerator = sum(
        (a - first_mean) * (b - second_mean)
        for a, b in zip(first_ranks, second_ranks)
    )

    first_denominator = sum(
        (a - first_mean) ** 2
        for a in first_ranks
    )

    second_denominator = sum(
        (b - second_mean) ** 2
        for b in second_ranks
    )

    denominator = (
        first_denominator *
        second_denominator
    ) ** 0.5

    if denominator == 0:
        return None

    return numerator / denominator