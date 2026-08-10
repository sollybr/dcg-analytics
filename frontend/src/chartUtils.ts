
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
}

export interface StatisticsDistribution {
    given: {
        field: string;
        value: string;
    };
    target: {
        field: string;
    };
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

export const createDistributionDataset = (
    distribution: DistributionItem[],
    targetField: string
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

    return {
        labels,
        datasets: [
            {
                label: 'Distribution',
                data,
                backgroundColor,
            },
        ],
    };
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
