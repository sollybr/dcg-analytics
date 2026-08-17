export interface DigimonCard {
  id?: string | number;
  cardNumber?: string;
  name?: {
    english?: string;
  } | string;
  color?: string | string[];
  colors?: string | string[];
  booster?: string;
  setId?: string;
  set?: string;
  setNumber?: string;
  cardType?: string | string[];
  type?: string | string[];
  types?: string | string[];
  level?: string | number | null;
  cardLevel?: string | number | null;
  rarity?: string;
  playCost?: string | number | null;
  dp?: string | number | null;
  form?: string;
  attribute?: string;
  effect?: string;
  digivolveEffect?: string;
  securityEffect?: string;
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

export const getCardColors = (
  cardOrColors: DigimonCard | string | string[] | undefined | null
): string[] => {
  let raw: string | string[] | undefined | null;

  if (
    typeof cardOrColors === 'object' &&
    !Array.isArray(cardOrColors) &&
    cardOrColors !== null
  ) {
    raw = cardOrColors.color || cardOrColors.colors;
  } else {
    raw = cardOrColors;
  }

  if (!raw) {
    return ['Unknown'];
  }

  if (Array.isArray(raw)) {
    return raw.map((color) => color.trim()).filter(Boolean);
  }

  if (typeof raw === 'string') {
    return raw
      .split('/')
      .map((color) => color.trim())
      .filter(Boolean);
  }

  return ['Unknown'];
};

export const getColors = (
  colors: string[] | undefined | null
): string[] => {
  if (!Array.isArray(colors)) {
    return [];
  }

  return colors.map((label) => {
    if (COLOR_MAP[label]) {
      return COLOR_MAP[label];
    }

    if (typeof label === 'string' && label.includes('/')) {
      const primary = label.split('/')[0].trim();
      return COLOR_MAP[primary] || COLOR_MAP.Unknown;
    }

    return COLOR_MAP.Unknown;
  });
};

export const getCardExpansion = (card: DigimonCard): string => {
  return (
    card.expansion_name ||
    card.expansionName ||
    card.expansion ||
    card.booster ||
    'Unknown Expansion'
  );
};

export const getCardTypes = (card: DigimonCard): string[] => {
  const raw = card.subtypes || card.type || card.types;

  if (!raw) {
    return [];
  }

  if (Array.isArray(raw)) {
    return raw.map((type) => type.trim()).filter(Boolean);
  }

  if (typeof raw === 'string') {
    return raw
      .split('/')
      .map((type) => type.trim())
      .filter(Boolean);
  }

  return [];
};

export const getCardLevel = (
  card: DigimonCard
): string | null => {
  const level = card.level ?? card.cardLevel;

  if (level === undefined || level === null || level === '-') {
    return null;
  }

  return String(level);
};