import { COLOR_MAP } from './cardUtils';

export const DISTINCT_COLORS_15 = [
    '#FF355E',
    '#FF6037',
    '#FF9966',
    '#FFCC33',
    '#CCFF00',
    '#66FF66',
    '#50BFE6',
    '#FF00CC',
    '#9933CC',
    '#333333',
    '#FBCEB1',
    '#00CCCC',
    '#8A2BE2',
    '#DE3163',
    '#40E0D0',
];

export const createInteractiveDatasets = (
    labels = [],
    dataArray = [],
    colorStrategy
) => {
    if (!Array.isArray(labels)) {
        return [];
    }

    return labels.map((label, index) => {
        let bgColor = '#ffffff';

        if (typeof colorStrategy === 'function') {
            bgColor = colorStrategy([label])[0];
        } else if (Array.isArray(colorStrategy)) {
            bgColor =
                colorStrategy[
                    index % colorStrategy.length
                ];
        } else if (typeof colorStrategy === 'string') {
            bgColor = colorStrategy;
        }

        return {
            label,
            data: labels.map((_, i) =>
                i === index
                    ? dataArray[index]
                    : null
            ),
            backgroundColor: bgColor,
        };
    });
};

export const createExpansionTypeDatasets = (
    labels = [],
    dataArray = [],
    expansionTypes = []
) => {
    if (
        !Array.isArray(labels) ||
        !Array.isArray(dataArray) ||
        !Array.isArray(expansionTypes)
    ) {
        return [];
    }

    const grouped = {};

    labels.forEach((label, index) => {
        const type =
            expansionTypes[index] || 'Other';

        if (!grouped[type]) {
            grouped[type] = {
                labels: [],
                data: [],
            };
        }

        grouped[type].labels.push(label);
        grouped[type].data.push(
            dataArray[index]
        );
    });

    return Object.entries(grouped).map(
        ([type, group], index) => ({
            label: type,
            data: labels.map((label) => {
                const groupIndex =
                    group.labels.indexOf(label);

                return groupIndex === -1
                    ? null
                    : group.data[groupIndex];
            }),
            backgroundColor:
                DISTINCT_COLORS_15[
                    index %
                    DISTINCT_COLORS_15.length
                ],
        })
    );
};

export interface DistributionItem {
    value: string;
    count: number;
    percentage: number;
    // Present when the backend was asked to include a baseline (default).
    // baseline_percentage = this value's share of the WHOLE card pool for
    // the target field, independent of the given condition. lift =
    // percentage / baseline_percentage -- 1.0 means "no different from the
    // overall base rate," >1 means over-represented, <1 under-represented.
    baseline_percentage?: number;
    lift?: number | null;
}

export interface StatisticsDistribution {
    given: {
        field: string;
        value: string;
    };
    target: {
        field: string;
    };
    // Total count the conditional distribution is based on. Always show
    // this next to any distribution chart -- a chart built on 4 cards
    // should not look the same as one built on 400.
    sample_size?: number;
    baseline_sample_size?: number;
    distribution: DistributionItem[];
}

export interface StatisticsField {
    name: string;
    type: 'categorical' | 'numeric' | 'text';
    django_type: string;
}

export interface StatisticsSchema {
    fields: Record<
        string,
        StatisticsField
    >;
    categorical_fields: string[];
}

export interface StatisticsAssociation {
    fields: {
        first: string;
        second: string;
    };
    cramers_v: number;
    // sample_size/reliable come from the chi-square expected-cell-count
    // check server-side. reliable === false means the contingency table
    // is too sparse for cramers_v to be trustworthy -- surface this
    // instead of letting a high V read as a confident finding.
    sample_size?: number;
    reliable?: boolean;
    low_expected_cell_ratio?: number | null;
}

export const getDistributionLabels = (
    distribution: DistributionItem[]
): string[] => {
    return distribution.map(
        (item) => item.value
    );
};

export const getDistributionValues = (
    distribution: DistributionItem[]
): number[] => {
    return distribution.map(
        (item) => item.count
    );
};

export const getDistributionPercentages = (
    distribution: DistributionItem[]
): number[] => {
    return distribution.map(
        (item) => item.percentage * 100
    );
};

export const getDistributionBaselinePercentages = (
    distribution: DistributionItem[]
): number[] => {
    return distribution.map(
        (item) => (item.baseline_percentage ?? 0) * 100
    );
};

export const getDistributionLift = (
    distribution: DistributionItem[]
): (number | null)[] => {
    return distribution.map(
        (item) => item.lift ?? null
    );
};

/**
 * A distribution item is only worth calling out as a "finding" if it's
 * both meaningfully sized (not 2 cards out of 4) and meaningfully skewed
 * relative to the baseline (lift far from 1.0). This intentionally
 * requires both baseline_percentage and a minimum sample size -- a lift
 * of 3.0x on n=2 is not a finding, it's noise.
 */
export const getNotableDistributionItems = (
    distribution: DistributionItem[],
    sampleSize: number | undefined,
    { minSampleSize = 20, minLift = 1.3, maxLift = 0.7 } = {}
): DistributionItem[] => {
    if (!sampleSize || sampleSize < minSampleSize) {
        return [];
    }

    return distribution.filter((item) => {
        if (item.lift == null) return false;
        return item.lift >= minLift || item.lift <= maxLift;
    });
};

export const createDistributionDataset = (
    distribution: DistributionItem[],
    targetField: string,
    { includeBaseline = false }: { includeBaseline?: boolean } = {}
) => {
    const labels =
        getDistributionLabels(distribution);

    const data =
        getDistributionValues(distribution);

    const backgroundColor =
        targetField === 'color'
            ? labels.map(
                (label) =>
                    COLOR_MAP[label] ||
                    COLOR_MAP.Unknown
            )
            : labels.map(
                (_, index) =>
                    DISTINCT_COLORS_15[
                        index %
                        DISTINCT_COLORS_15.length
                    ]
            );

    const datasets: Array<Record<string, unknown>> = [
        {
            label: 'Distribution',
            data,
            backgroundColor,
        },
    ];

    // Opt-in second dataset showing the full-card-pool baseline as a
    // muted overlay, so the skew is visible on the chart itself rather
    // than requiring the viewer to read lift numbers separately.
    if (includeBaseline) {
        const hasBaseline = distribution.some(
            (item) => item.baseline_percentage !== undefined
        );

        if (hasBaseline) {
            datasets.push({
                label: 'Baseline (all cards)',
                data: getDistributionBaselinePercentages(distribution),
                backgroundColor: 'rgba(148, 163, 184, 0.35)',
                borderColor: 'rgba(148, 163, 184, 0.8)',
                borderWidth: 1,
            });
        }
    }

    return {
        labels,
        datasets,
    };
};

/**
 * Human-readable reliability note for an association result. Returns
 * null when the result is reliable (nothing to warn about) or when
 * reliability info isn't present (older response shape).
 */
export const getAssociationReliabilityWarning = (
    association: StatisticsAssociation
): string | null => {
    if (association.reliable === undefined) {
        return null;
    }

    if (association.reliable) {
        return null;
    }

    const n = association.sample_size ?? 'unknown';
    return `Low confidence: sample size (n=${n}) is too small relative to the number of category combinations for this association to be reliable.`;
};

export const darkOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#00f3ff',
                font: {
                    family:
                        "'Pixel Digivolve', monospace",
                },
            },
        },
    },
    scales: {
        x: {
            ticks: {
                color: '#00f3ff',
                font: {
                    family:
                        "'Pixel Digivolve', monospace",
                },
            },
            grid: {
                color: '#1e293b',
            },
        },
        y: {
            ticks: {
                color: '#00f3ff',
                font: {
                    family:
                        "'Pixel Digivolve', monospace",
                },
            },
            grid: {
                color: '#1e293b',
            },
        },
    },
};

export const stackedDarkOptions = {
    ...darkOptions,
    scales: {
        x: {
            ...darkOptions.scales.x,
            stacked: true,
        },
        y: {
            ...darkOptions.scales.y,
            stacked: true,
        },
    },
};
