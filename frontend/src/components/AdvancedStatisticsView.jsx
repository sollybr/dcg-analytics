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

const FIELD_OPTIONS = [
    'name',
    'color',
    'rarity',
    'expansion',
    'subtype',
];

const getFieldLabel = (field) => {
    const labels = {
        name: 'CARD NAME',
        color: 'COLOR',
        rarity: 'RARITY',
        expansion: 'EXPANSION',
        subtype: 'TYPE (TRAIT)',
    };

    return labels[field] || field.toUpperCase();
};

export default function AdvancedStatisticsView({ onClose }) {
    const [givenField, setGivenField] = useState('');
    const [targetField, setTargetField] = useState('');
    const [selectedValue, setSelectedValue] = useState('');

    const [distribution, setDistribution] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Any of the FIELD_OPTIONS pairs with any other -- this replaces the
    // fixed 8-pair preset list, which only covered some directions
    // (e.g. had RARITY → COLOR but not COLOR → RARITY). Deriving this
    // from two independent selects means every direction is available,
    // and downstream code below still just reads .given/.target/.label
    // the same way it did off the old preset objects.
    const selectedPreset =
        givenField && targetField && givenField !== targetField
            ? {
                given: givenField,
                target: targetField,
                label: `${getFieldLabel(givenField)} → ${getFieldLabel(targetField)}`,
                description: `See how ${getFieldLabel(targetField)} is distributed for a given ${getFieldLabel(givenField)}.`,
            }
            : null;

    const swapFields = () => {
        setGivenField(targetField);
        setTargetField(givenField);
        setSelectedValue('');
        setDistribution(null);
        setError(null);
    };

    const resetAnalysis = () => {
        setGivenField('');
        setTargetField('');
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
                                    BUILD ANALYSIS
                                </h2>
                            </div>

                            <span>
                                {FIELD_OPTIONS.length}
                                {' '}FIELDS
                            </span>
                        </div>

                        <div className="distribution-pair-builder">
                            <div className="pair-field">
                                <label htmlFor="given-field-select">
                                    GIVEN
                                </label>

                                <select
                                    id="given-field-select"
                                    value={givenField}
                                    onChange={(event) =>
                                        setGivenField(event.target.value)
                                    }
                                >
                                    <option value="">
                                        SELECT FIELD...
                                    </option>

                                    {FIELD_OPTIONS.map((field) => (
                                        <option
                                            key={field}
                                            value={field}
                                            disabled={field === targetField}
                                        >
                                            {getFieldLabel(field)}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                type="button"
                                className="pair-swap-button"
                                onClick={swapFields}
                                disabled={!givenField || !targetField}
                                title="Swap given and target"
                            >
                                ⇄
                            </button>

                            <div className="pair-field">
                                <label htmlFor="target-field-select">
                                    TARGET
                                </label>

                                <select
                                    id="target-field-select"
                                    value={targetField}
                                    onChange={(event) =>
                                        setTargetField(event.target.value)
                                    }
                                >
                                    <option value="">
                                        SELECT FIELD...
                                    </option>

                                    {FIELD_OPTIONS.map((field) => (
                                        <option
                                            key={field}
                                            value={field}
                                            disabled={field === givenField}
                                        >
                                            {getFieldLabel(field)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {givenField && targetField && (
                            <p className="query-description">
                                {`See how ${getFieldLabel(targetField)} is distributed for a given ${getFieldLabel(givenField)}.`}
                            </p>
                        )}
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