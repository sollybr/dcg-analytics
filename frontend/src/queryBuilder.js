// queryBuilder.js
//
// Generic across any endpoint/registry pair. Nobody needs to modify this
// file to add a new filter -- it just walks whatever registry it's given.
export function buildQueryParams(filterRegistry, values) {
    const params = new URLSearchParams();

    for (const [key, paramName] of Object.entries(filterRegistry)) {
        const value = values[key];
        if (Array.isArray(value) && value.length > 0) {
            params.append(paramName, value.join(','));
        }
    }

    return params;
}