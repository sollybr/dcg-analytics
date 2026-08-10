
export async function fetchAnalytics() {
    const response = await fetch('/api/analytics/');

    if (!response.ok) {
        throw new Error(`Analytics API returned ${response.status}`);
    }

    return response.json();
}

export async function fetchCardsByName(name) {
    const encodedName = encodeURIComponent(name);
    const response = await fetch(`/api/cards/?name=${encodedName}`);

    if (!response.ok) {
        throw new Error(`Cards API returned ${response.status}`);
    }

    return response.json();
}

export async function fetchCardsByType(type, page = 1) {
    const encodedType = encodeURIComponent(type);
    const response = await fetch(
        `/api/cards-by-type/?type=${encodedType}&page=${page}`
    );

    if (!response.ok) {
        throw new Error(`Cards by Type API returned ${response.status}`);
    }

    return response.json();
}

export async function fetchStatisticsSchema() {
    const response = await fetch('/api/statistics/schema/');

    if (!response.ok) {
        throw new Error(
            `Statistics Schema API returned ${response.status}`
        );
    }

    return response.json();
}

export async function fetchStatisticsDistribution(
    given,
    value,
    target
) {
    const params = new URLSearchParams({
        given,
        value,
        target,
    });

    const response = await fetch(
        `/api/statistics/distribution/?${params}`
    );

    if (!response.ok) {
        throw new Error(
            `Statistics Distribution API returned ${response.status}`
        );
    }

    return response.json();
}

export async function fetchStatisticsAssociation(
    first,
    second
) {
    const params = new URLSearchParams({
        first,
        second,
    });

    const response = await fetch(
        `/api/statistics/association/?${params}`
    );

    if (!response.ok) {
        throw new Error(
            `Statistics Association API returned ${response.status}`
        );
    }

    return response.json();
}
