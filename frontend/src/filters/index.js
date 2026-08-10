// filters/index.js
//
// Aggregates every known filter into one registry object. Registering a
// new filter is a single new import + a single new line in ANALYTICS_FILTERS
// below -- both are additive, so two people registering different filters
// in parallel merge cleanly (worst case: a trivial two-line merge, never a
// rewrite of shared conditional logic).
import { expansionFilter } from './expansion';
import { subtypeFilter } from './subtype';

export const ANALYTICS_FILTERS = {
    [expansionFilter.key]: expansionFilter.paramName,
    [subtypeFilter.key]: subtypeFilter.paramName,
};