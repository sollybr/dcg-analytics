from collections import Counter
from math import sqrt


def _split_values(raw):
    """
    Same tokenization rule as distributions.py: multi-value fields
    (color, subtype, type, card_type) store values like "Red/Blue" and
    should be split on '/' rather than treated as one combined category.
    Used here so a two-way table crosses INDIVIDUAL values, not raw
    strings -- otherwise "Red/Blue" would be its own category distinct
    from both "Red" and "Blue", and would never match up with how
    distributions.py counts the same field.
    """
    if not raw:
        return []

    tokens = []
    for val in str(raw).split("/"):
        cleaned = val.strip()
        if cleaned and cleaned != "-":
            tokens.append(cleaned)

    return tokens


def contingency_table(rows, first_field, second_field):
    """
    Builds the two-way table by crossing every split token of
    first_field against every split token of second_field for each row.
    NOTE: a card with two colors and two subtypes now contributes 4
    cell increments (2x2 cartesian product), not 1. That means the
    total N behind this table is "value-pair occurrences," not "cards" --
    cramers_v_with_diagnostics's sample_size reflects that, not a card
    count. This is the same tradeoff distributions.py already makes on
    a single field; here it just applies to both dimensions at once.
    """
    table = {}

    for row in rows:
        first_tokens = _split_values(row.get(first_field))
        second_tokens = _split_values(row.get(second_field))

        if not first_tokens or not second_tokens:
            continue

        for first in first_tokens:
            table.setdefault(first, Counter())
            for second in second_tokens:
                table[first][second] += 1

    return table


def cramers_v(rows, first_field, second_field):
    """Unchanged signature/behavior -- returns just the float, as before."""
    return cramers_v_with_diagnostics(rows, first_field, second_field)["cramers_v"]


def cramers_v_with_diagnostics(rows, first_field, second_field, min_expected_cell=5):
    """
    Same chi-square/Cramer's V calc as before, plus:
      - sample_size: total N the statistic is based on
      - low_expected_cell_ratio: fraction of contingency-table cells with
        expected count < min_expected_cell (the standard chi-square rule
        of thumb is that >20% of cells falling below this makes the
        approximation unreliable)
      - reliable: bool, convenience flag for the above
    A high Cramer's V computed over a sparse table (small N spread across
    many category combinations) can be an artifact rather than a real
    association -- this surfaces that instead of silently returning a
    single confident-looking number.
    """
    table = contingency_table(rows, first_field, second_field)

    empty_result = {
        "cramers_v": 0.0,
        "sample_size": 0,
        "low_expected_cell_ratio": None,
        "reliable": False,
    }

    if not table:
        return empty_result

    row_keys = list(table.keys())
    column_keys = sorted({column for row in table.values() for column in row})

    total = sum(table[row][column] for row in row_keys for column in column_keys)

    if total == 0:
        return empty_result

    row_totals = {row: sum(table[row].values()) for row in row_keys}
    column_totals = {
        column: sum(table[row][column] for row in row_keys) for column in column_keys
    }

    chi_squared = 0.0
    low_expected_cells = 0
    total_cells = 0

    for row in row_keys:
        for column in column_keys:
            observed = table[row][column]
            expected = row_totals[row] * column_totals[column] / total

            total_cells += 1
            if expected < min_expected_cell:
                low_expected_cells += 1

            if expected > 0:
                chi_squared += (observed - expected) ** 2 / expected

    n = total
    phi_squared = chi_squared / n

    rows_count = len(row_keys)
    columns_count = len(column_keys)
    correction = min(rows_count - 1, columns_count - 1)

    v = sqrt(phi_squared / correction) if correction > 0 else 0.0
    low_expected_cell_ratio = low_expected_cells / total_cells if total_cells else None

    return {
        "cramers_v": v,
        "sample_size": n,
        "low_expected_cell_ratio": low_expected_cell_ratio,
        "reliable": (low_expected_cell_ratio is not None and low_expected_cell_ratio <= 0.2),
    }