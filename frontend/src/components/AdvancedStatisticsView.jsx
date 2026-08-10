
import { useState } from 'react';
import { Bar } from 'react-chartjs-2';

import {
    fetchStatisticsDistribution,
} from '../api';

import {
    createDistributionDataset,
    stackedDarkOptions,
} from '../chartUtils';

import AnalyticsChart from './AnalyticsChart';

const distributionPresets = [
    {
        id: 'name-color',
        label: 'CARD NAME → COLOR',
        given: 'name',
        target: 'color',
        description: 'Discover the color composition of a specific card name.',
    },
    {
        id: 'name-rarity',
        label: 'CARD NAME → RARITY',
        given: 'name',
        target: 'rarity',
        description: 'See how a card name is distributed across rarities.',
    },
    {
        id: 'name-expansion',
        label: 'CARD NAME → EXPANSION',
        given: 'name',
        target: 'expansion',
        description: 'Track where a card name has appeared across expansions.',
    },
    {
        id: 'expansion-color',
        label: 'EXPANSION → COLOR',
        given: 'expansion',
        target: 'color',
        description: 'Analyze the color composition of an expansion.',
    },
    {
        id: 'expansion-rarity',
        label: 'EXPANSION → RARITY',
        given: 'expansion',
        target: 'rarity',
        description: 'Analyze the rarity distribution of an expansion.',
    },
    {
        id: 'color-type',
        label: 'COLOR → CARD TYPE',
        given: 'color',
        target: 'card_type',
        description: 'Discover which card types dominate a color.',
    },
    {
        id: 'rarity-color',
        label: 'RARITY → COLOR',
        given: 'rarity',
        target: 'color',
        description: 'Analyze the color composition of a rarity.',
    },
    {
        id: 'type-rarity',
        label: 'CARD TYPE → RARITY',
        given: 'card_type',
        target: 'rarity',
        description: 'See how card types are distributed across rarities.',
    },
];

const getFieldLabel = (field) => {
    const labels = {
        name: 'CARD NAME',
        color: 'COLOR',
        rarity: 'RARITY',
        expansion: 'EXPANSION',
        card_type: 'CARD TYPE',
    };

    return labels[field] || field.toUpperCase();
};

export default function AdvancedStatisticsView({ onClose }) {
    const [selectedPreset, setSelectedPreset] = useState(null);
    const [selectedValue, setSelectedValue] = useState('');

    const [distribution, setDistribution] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const selectPreset = (preset) => {
        setSelectedPreset(preset);
        setSelectedValue('');
        setDistribution(null);
        setError(null);
    };

    const resetAnalysis = () => {
        setSelectedPreset(null);
        setSelectedValue('');
        setDistribution(null);
        setError(null);
    };

    const analyzeDistribution = async () => {
        const value = selectedValue.trim();

        if (!selectedPreset || !value) {
            return;
        }

        setLoading(true);
        setError(null);
        setDistribution(null);

        try {
            const result =
                await fetchStatisticsDistribution(
                    selectedPreset.given,
                    value,
                    selectedPreset.target
                );

            if (
                !result ||
                !Array.isArray(result.distribution)
            ) {
                throw new Error(
                    'Invalid distribution response from API.'
                );
            }

            setDistribution(result);
        } catch (error) {
            console.error(
                'Error fetching statistics distribution:',
                error
            );

            setError(
                error.message ||
                'Unable to calculate distribution.'
            );
        } finally {
            setLoading(false);
        }
    };

    const distributionItems =
        distribution?.distribution || [];

    const totalObservations =
        distributionItems.reduce(
            (total, item) =>
                total + Number(item.count || 0),
            0
        );

    const dominantItem =
        distributionItems.length > 0
            ? distributionItems[0]
            : null;

    const chartData =
        distribution && selectedPreset
            ? {
                ...createDistributionDataset(
                    distribution.distribution,
                    selectedPreset.target
                ),
                datasets:
                    createDistributionDataset(
                        distribution.distribution,
                        selectedPreset.target
                    ).datasets.map(
                        (dataset) => ({
                            ...dataset,
                            label: `${getFieldLabel(
                                selectedPreset.target
                            )} DISTRIBUTION (%)`,
                            data:
                                distributionItems.map(
                                    (item) =>
                                        Number(
                                            item.percentage
                                        ) * 100
                                ),
                        })
                    ),
            }
            : null;

    const chartOptions = {
        ...stackedDarkOptions,
        indexAxis: 'y',
        plugins: {
            ...stackedDarkOptions.plugins,
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: (context) =>
                        `${context.parsed.x.toFixed(2)}%`,
                },
            },
        },
        scales: {
            x: {
                ...stackedDarkOptions.scales.x,
                beginAtZero: true,
                max: 100,
                ticks: {
                    ...stackedDarkOptions.scales.x.ticks,
                    callback: (value) =>
                        `${value}%`,
                },
            },
            y: {
                ...stackedDarkOptions.scales.y,
            },
        },
    };

    return (
        <div className="digi-dashboard">
            <section className="advanced-statistics">

                <div className="advanced-statistics-header">
                    <div>
                        <span className="statistics-eyebrow">
                            DIGITAL WORLD DATABASE
                        </span>

                        <h1>
                            ADVANCED STATISTICS
                        </h1>

                        <p>
                            Explore conditional
                            distributions across
                            the card database.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="digi-menu-button"
                        onClick={onClose}
                    >
                        BACK TO HOME
                    </button>
                </div>

                {!selectedPreset && (
                    <section className="advanced-statistics-menu">
                        <div className="statistics-section-header">
                            <div>
                                <span>
                                    ANALYSIS MODULE
                                </span>

                                <h2>
                                    QUICK ANALYSIS
                                </h2>
                            </div>

                            <span>
                                {distributionPresets.length}
                                {' '}AVAILABLE
                            </span>
                        </div>

                        <div className="distribution-presets">
                            {distributionPresets.map(
                                (preset) => (
                                    <button
                                        key={preset.id}
                                        type="button"
                                        className="distribution-preset"
                                        onClick={() =>
                                            selectPreset(
                                                preset
                                            )
                                        }
                                    >
                                        <span className="preset-label">
                                            {preset.label}
                                        </span>

                                        <span className="preset-description">
                                            {
                                                preset.description
                                            }
                                        </span>

                                        <span className="preset-arrow">
                                            →
                                        </span>
                                    </button>
                                )
                            )}
                        </div>
                    </section>
                )}

                {selectedPreset && (
                    <>
                        <section className="advanced-statistics-query">
                            <div className="query-header">
                                <div>
                                    <span>
                                        SELECTED ANALYSIS
                                    </span>

                                    <h2>
                                        {selectedPreset.label}
                                    </h2>
                                </div>

                                <button
                                    type="button"
                                    className="statistics-reset-button"
                                    onClick={
                                        resetAnalysis
                                    }
                                >
                                    CHANGE ANALYSIS
                                </button>
                            </div>

                            <p className="query-description">
                                {
                                    selectedPreset.description
                                }
                            </p>

                            <div className="query-form">
                                <div className="query-field">
                                    <label
                                        htmlFor="statistics-value"
                                    >
                                        {getFieldLabel(
                                            selectedPreset.given
                                        )}
                                    </label>

                                    <input
                                        id="statistics-value"
                                        type="text"
                                        value={
                                            selectedValue
                                        }
                                        onChange={(
                                            event
                                        ) =>
                                            setSelectedValue(
                                                event.target
                                                    .value
                                            )
                                        }
                                        placeholder={`ENTER ${getFieldLabel(
                                            selectedPreset.given
                                        )}`}
                                        autoComplete="off"
                                        onKeyDown={(
                                            event
                                        ) => {
                                            if (
                                                event.key ===
                                                'Enter'
                                            ) {
                                                analyzeDistribution();
                                            }
                                        }}
                                    />
                                </div>

                                <div className="query-target">
                                    <span>
                                        TARGET
                                    </span>

                                    <strong>
                                        {getFieldLabel(
                                            selectedPreset.target
                                        )}
                                    </strong>
                                </div>

                                <button
                                    type="button"
                                    className="digi-menu-button"
                                    onClick={
                                        analyzeDistribution
                                    }
                                    disabled={
                                        loading ||
                                        !selectedValue.trim()
                                    }
                                >
                                    {loading
                                        ? 'ANALYZING...'
                                        : 'RUN ANALYSIS'}
                                </button>
                            </div>
                        </section>

                        {error && (
                            <section className="advanced-statistics-error">
                                <span>
                                    ANALYSIS FAILURE
                                </span>

                                <h2>
                                    DATABASE QUERY FAILED
                                </h2>

                                <p>{error}</p>
                            </section>
                        )}

                        {loading && (
                            <section className="advanced-statistics-loading">
                                <div className="digi-spinner"></div>

                                <p>
                                    CALCULATING
                                    DISTRIBUTION...
                                </p>
                            </section>
                        )}

                        {distribution &&
                            !loading && (
                                <>
                                    {distributionItems.length ===
                                    0 ? (
                                        <section className="advanced-statistics-empty">
                                            <span>
                                                NO OBSERVATIONS
                                            </span>

                                            <h2>
                                                NO DATA FOUND
                                            </h2>

                                            <p>
                                                No records matched
                                                <strong>
                                                    {' '}
                                                    "
                                                    {
                                                        distribution
                                                            .given
                                                            .value
                                                    }
                                                    "
                                                </strong>
                                                .
                                            </p>
                                        </section>
                                    ) : (
                                        <>
                                            <section className="statistics-summary">
                                                <div className="statistics-metric">
                                                    <span>
                                                        OBSERVATIONS
                                                    </span>

                                                    <strong>
                                                        {
                                                            totalObservations
                                                        }
                                                    </strong>
                                                </div>

                                                <div className="statistics-metric">
                                                    <span>
                                                        CATEGORIES
                                                    </span>

                                                    <strong>
                                                        {
                                                            distributionItems.length
                                                        }
                                                    </strong>
                                                </div>

                                                <div className="statistics-metric">
                                                    <span>
                                                        DOMINANT
                                                    </span>

                                                    <strong>
                                                        {
                                                            dominantItem
                                                                ?.value
                                                        }
                                                    </strong>
                                                </div>

                                                <div className="statistics-metric">
                                                    <span>
                                                        DOMINANT SHARE
                                                    </span>

                                                    <strong>
                                                        {(
                                                            Number(
                                                                dominantItem
                                                                    ?.percentage ||
                                                                    0
                                                            ) *
                                                            100
                                                        ).toFixed(
                                                            2
                                                        )}
                                                        %
                                                    </strong>
                                                </div>
                                            </section>

                                            <section className="advanced-statistics-result">
                                                <AnalyticsChart
                                                    title={`${getFieldLabel(
                                                        selectedPreset.target
                                                    )} DISTRIBUTION — ${
                                                        distribution
                                                            .given
                                                            .value
                                                    }`}
                                                >
                                                    <Bar
                                                        data={
                                                            chartData
                                                        }
                                                        options={
                                                            chartOptions
                                                        }
                                                    />
                                                </AnalyticsChart>

                                                <div className="distribution-results">
                                                    <div className="distribution-results-header">
                                                        <span>
                                                            VALUE
                                                        </span>

                                                        <span>
                                                            COUNT
                                                        </span>

                                                        <span>
                                                            SHARE
                                                        </span>
                                                    </div>

                                                    {distributionItems.map(
                                                        (
                                                            item,
                                                            index
                                                        ) => {
                                                            const percentage =
                                                                Number(
                                                                    item.percentage
                                                                ) *
                                                                100;

                                                            return (
                                                                <div
                                                                    className="distribution-result"
                                                                    key={
                                                                        item.value
                                                                    }
                                                                >
                                                                    <div className="distribution-value">
                                                                        <span className="distribution-rank">
                                                                            {String(
                                                                                index +
                                                                                    1
                                                                            ).padStart(
                                                                                2,
                                                                                '0'
                                                                            )}
                                                                        </span>

                                                                        <strong>
                                                                            {
                                                                                item.value
                                                                            }
                                                                        </strong>
                                                                    </div>

                                                                    <span>
                                                                        {
                                                                            item.count
                                                                        }
                                                                    </span>

                                                                    <div className="distribution-percentage">
                                                                        <div className="distribution-bar">
                                                                            <div
                                                                                className="distribution-bar-fill"
                                                                                style={{
                                                                                    width: `${percentage}%`,
                                                                                }}
                                                                            />
                                                                        </div>

                                                                        <span>
                                                                            {percentage.toFixed(
                                                                                2
                                                                            )}
                                                                            %
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            );
                                                        }
                                                    )}
                                                </div>
                                            </section>
                                        </>
                                    )}
                                </>
                            )}
                    </>
                )}
            </section>
        </div>
    );
}
