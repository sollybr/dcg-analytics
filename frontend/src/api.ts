import { ANALYTICS_FILTERS } from './filters';
import { buildQueryParams } from './queryBuilder';
import type { FieldName } from './fieldOptions';

export async function fetchAnalytics(filters = {}) {
    const params = buildQueryParams(ANALYTICS_FILTERS, filters);
    const url = params.toString()
        ? `/api/analytics/?${params.toString()}`
        : '/api/analytics/';

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Analytics API returned ${response.status}`);
    }

    return response.json();
}

export async function fetchCardsByName(
    name: string,
    signal?: AbortSignal
): Promise<unknown> {
    const res = await fetch(`/api/cards/?name=${encodeURIComponent(name)}`, { signal });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return res.json();
}

export async function fetchCardsByType(
    type: string,
    page = 1,
    signal?: AbortSignal
) {
    const encodedType = encodeURIComponent(type);
    const response = await fetch(
        `/api/cards-by-type/?type=${encodedType}&page=${page}`,
        { signal }
    );

    if (!response.ok) {
        throw new Error(`Cards by Type API returned ${response.status}`);
    }

    return response.json();
}

export interface FieldOption {
    value: string;
    label?: string;
    count: number;
}

export interface FieldOptionsResponse {
    field: string;
    options: FieldOption[];
}

export async function fetchFieldOptions(
    field: FieldName,
    query = '',
    signal?: AbortSignal,
    limit = 20
): Promise<FieldOptionsResponse> {
    const params = new URLSearchParams({
        field,
        limit: String(limit),
    });

    if (query) {
        params.set('q', query);
    }

    const response = await fetch(
        `/api/field-options/?${params}`,
        { signal }
    );

    if (!response.ok) {
        throw new Error(
            `Field Options API returned ${response.status}`
        );
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
    given: string,
    value: string,
    target: string
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
    first: string,
    second: string
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