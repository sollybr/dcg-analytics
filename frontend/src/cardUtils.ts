
// Define the shape of the card data based on the API's varied schema
export interface DigimonCard {
  id?: string;
  cardNumber?: string;

  name?: {
    english?: string;
    [key: string]: string | undefined;
  };

  color?: string | string[];
  colors?: string[];

  booster?: string;
  setId?: string;
  setNumber?: string;
  set?: string;

  notes?: string;
  rarity?: string;
  playCost?: string | number;

  restrictions?: {
    english?: string;
    [key: string]: string | undefined;
  };

  [key: string]: any;
}

export const COLOR_MAP: Record<string, string> = {
  Red: '#ef4444',
  Blue: '#3b82f6',
  Yellow: '#eab308',
  Green: '#22c55e',
  Black: '#475569',
  Purple: '#a855f7',
  White: '#f8fafc',
  Unknown: '#64748b',
};

export const DISTINCT_COLORS_15: string[] = [
  '#FF355E',
  '#FF6037',
  '#FF9966',
  '#FFCC33',
  '#CCFF00',
  '#66FF66',
  '#50BFE6',
  '#0099FF',
  '#9C51B6',
  '#FF00CC',
  '#FF6080',
  '#FF9E2C',
  '#A7F432',
  '#00E5FF',
  '#B57EDC',
];

export const getCardColors = (
  colorField?: string | string[]
): string[] => {
  if (!colorField) {
    return ['Unknown'];
  }

  if (Array.isArray(colorField)) {
    return colorField.length > 0
      ? colorField
      : ['Unknown'];
  }

  if (typeof colorField === 'string') {
    const splitColors = colorField
      .split('/')
      .map((color) => color.trim())
      .filter(Boolean);

    return splitColors.length > 0
      ? splitColors
      : ['Unknown'];
  }

  return ['Unknown'];
};

export const getCardExpansion = (
  card: DigimonCard
): string => {
  const expansion =
    card.booster ||
    card.setId ||
    card.setNumber ||
    card.set;

  if (expansion && expansion !== '-') {
    return expansion;
  }

  if (
    card.cardNumber &&
    card.cardNumber.includes('-')
  ) {
    return card.cardNumber.split('-')[0];
  }

  return 'Unknown';
};

/**
 * Returns the card's `type` field.
 *
 * Example:
 * type: "Reptile/Dragon"
 *
 * returns:
 * ["Reptile", "Dragon"]
 */
export const getCardTypes = (
  card: DigimonCard
): string[] => {
  if (
    typeof card.type !== 'string' ||
    !card.type ||
    card.type === '-'
  ) {
    return [];
  }

  return card.type
    .split('/')
    .map((type: string) => type.trim())
    .filter(
      (type: string) =>
        type.length > 0 &&
        type !== '-'
    );
};

export const getCardLevel = (
  card: DigimonCard
): number | null => {
  const levelKeyRegex =
    /^(level|lv|stage|digimon[_\s]?lev(el)?)$/i;

  for (const key of Object.keys(card)) {
    if (!levelKeyRegex.test(key)) {
      continue;
    }

    const value = card[key];

    if (
      value === undefined ||
      value === null ||
      value === '-' ||
      value === ''
    ) {
      continue;
    }

    if (typeof value === 'number') {
      return isNaN(value) ? null : value;
    }

    if (typeof value === 'string') {
      const match = value.match(/([0-9]+)/);

      if (match) {
        const parsed = parseInt(match[1], 10);
        return isNaN(parsed) ? null : parsed;
      }
    }
  }

  return null;
};

export const getCardSubtypes = (
  card: DigimonCard
): string[] => {
  const subtypeKeyRegex =
    /^(subtypes?|subtype|cardType|type)$/i;

  const results = new Set<string>();

  for (const key of Object.keys(card)) {
    if (!subtypeKeyRegex.test(key)) {
      continue;
    }

    const field = card[key];

    if (!field) {
      continue;
    }

    if (Array.isArray(field)) {
      field.forEach((value: unknown) => {
        if (typeof value !== 'string') {
          return;
        }

        value.split('/').forEach((part) => {
          const cleaned = part.trim();

          if (
            cleaned &&
            cleaned !== '-'
          ) {
            results.add(cleaned);
          }
        });
      });
    } else if (typeof field === 'string') {
      field.split('/').forEach((part) => {
        const cleaned = part.trim();

        if (
          cleaned &&
          cleaned !== '-'
        ) {
          results.add(cleaned);
        }
      });
    }
  }

  return Array.from(results);
};
