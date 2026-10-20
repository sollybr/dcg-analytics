// Fields the backend can return distinct values for. Keep in sync with the
// whitelist in the /api/field-options/ view.
export const DEFAULT_FIELD_OPTIONS = [
    'name',
    'color',
    'rarity',
    'expansion',
    'subtype',
    'card_type',
] as const;

export type FieldName = (typeof DEFAULT_FIELD_OPTIONS)[number];
