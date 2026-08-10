from collections import Counter
from math import sqrt


def contingency_table(rows, first_field, second_field):
    table = {}

    for row in rows:
        first = row.get(first_field)
        second = row.get(second_field)

        if first in (None, "") or second in (None, ""):
            continue

        table.setdefault(first, Counter())
        table[first][second] += 1

    return table


def cramers_v(rows, first_field, second_field):
    table = contingency_table(
        rows,
        first_field,
        second_field,
    )

    if not table:
        return 0.0

    row_keys = list(table.keys())
    column_keys = sorted({
        column
        for row in table.values()
        for column in row
    })

    total = sum(
        table[row][column]
        for row in row_keys
        for column in column_keys
    )

    if total == 0:
        return 0.0

    row_totals = {
        row: sum(table[row].values())
        for row in row_keys
    }

    column_totals = {
        column: sum(
            table[row][column]
            for row in row_keys
        )
        for column in column_keys
    }

    chi_squared = 0.0

    for row in row_keys:
        for column in column_keys:
            observed = table[row][column]

            expected = (
                row_totals[row] *
                column_totals[column] /
                total
            )

            if expected > 0:
                chi_squared += (
                    (observed - expected) ** 2
                    / expected
                )

    n = total
    phi_squared = chi_squared / n

    rows_count = len(row_keys)
    columns_count = len(column_keys)

    correction = min(
        rows_count - 1,
        columns_count - 1,
    )

    if correction <= 0:
        return 0.0

    return sqrt(phi_squared / correction)