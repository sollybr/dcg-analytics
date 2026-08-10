def distribution_response(
    given_field,
    given_value,
    target_field,
    distribution,
):
    return {
        "given": {
            "field": given_field,
            "value": given_value,
        },
        "target": {
            "field": target_field,
        },
        "distribution": distribution,
    }


def statistic_response(
    statistic,
    value,
    **metadata,
):
    return {
        "statistic": statistic,
        "value": value,
        **metadata,
    }