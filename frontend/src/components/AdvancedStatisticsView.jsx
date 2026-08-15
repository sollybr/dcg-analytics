import { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';

import {
    fetchStatisticsDistribution,
    fetchStatisticsAssociation,
    fetchStatisticsSchema,
} from '../api';

import {
    createDistributionDataset,
    stackedDarkOptions,
    getNotableDistributionItems,
    getAssociationReliabilityWarning,
} from '../chartUtils';

import AnalyticsChart from './AnalyticsChart';

// Used only until /api/statistics/schema/ resolves, or if that request
// fails -- keeps the picker usable without a network round trip blocking
// first render, and gives a safe fallback if the schema endpoint is down.
const DEFAULT_FIELD_OPTIONS = [
    'name',
    'color',
    'rarity',
    'expansion',
    'subtype',
    'card_type',
];

// Fields the backend schema will report as "categorical" (any CharField)
// but that aren't meaningful as a statistics dimension -- card_number is
// close to a primary key, so "card_number -> color" would just report
// ~100% for whatever one card happens to be. Filtered out client-side
// since this is a domain judgment schema.py has no way to encode.
const NON_ANALYTIC_FIELDS = ['card_number'];

const FIELD_LABELS = {
    name: 'CARD NAME',
    color: 'COLOR',
    rarity: 'RARITY',
    expansion: 'EXPANSION',
    subtype: 'TYPE (TRAIT)',
    card_type: 'CARD TYPE',
};

const getFieldLabel = (field) => {
    return FIELD_LABELS[field] || field.toUpperCase();
};

export default function AdvancedStatisticsView({ onClose }) {
    const [fieldOptions, setFieldOptions] = useState(DEFAULT_FIELD_OPTIONS);
    const [givenField, setGivenField] = useState('');
    const [targetField, setTargetField] = useState('');
    const [selectedValue, setSelectedValue] = useState('');

    const [distribution, setDistribution] = useState(null);
    const [association, setAssociation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Pull the real field list from the backend so the picker stays in
    // sync with schema.py rather than a hand-maintained duplicate. Falls
    // back to DEFAULT_FIELD_OPTIONS on failure so the view still works.
    useEffect(() => {
        let cancelled = false;

        fetchStatisticsSchema()
            .then((schema) => {
                if (cancelled) return;

                const categorical = Array.isArray(
                    schema?.categorical_fields
                )
                    ? schema.categorical_fields.filter(
                        (field) => !NON_ANALYTIC_FIELDS.includes(field)
                    )
                    : [];

                if (categorical.length > 0) {
                    setFieldOptions(categorical);
                }
            })
            .catch((err) => {
                console.error(
                    'Failed to load statistics schema, using default field list:',
                    err
                );
            });

        return () => {
            cancelled = true;
        };
    }, []);

    // Any of the fetched fieldOptions pairs with any other -- this replaces the
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
        setAssociation(null);
        setError(null);
    };

    const resetAnalysis = () => {
        setGivenField('');
        setTargetField('');
        setSelectedValue('');
        setDistribution(null);
        setAssociation(null);
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
        setAssociation(null);

        try {
            // The distribution answers "for this one given VALUE, how is
            // the target split, and is that split unusual vs. the whole
            // card pool." The association answers a different question --
            // "across the ENTIRE dataset, how strongly related are these
            // two FIELDS in general, and is that reading trustworthy."
            // They're complementary, not duplicates, so both get shown.
            // Association is best-effort: if it fails, the distribution
            // result should still render rather than the whole analysis
            // erroring out.
            const [distResult, assocResult] = await Promise.all([
                fetchStatisticsDistribution(
                    selectedPreset.given,
                    value,
                    selectedPreset.target
                ),
                fetchStatisticsAssociation(
                    selectedPreset.given,
                    selectedPreset.target
                ).catch((assocError) => {
                    console.error(
                        'Association fetch failed (non-fatal):',
                        assocError
                    );
                    return null;
                }),
            ]);

            if (
                !distResult ||
                !Array.isArray(distResult.distribution)
            ) {
                throw new Error(
                    'Invalid distribution response from API.'
                );
            }

            setDistribution(distResult);
            setAssociation(assocResult);
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

    // Prefer the backend's real sample_size (total tokenized value
    // count) over summing client-side, since they can diverge slightly
    // for multi-value fields -- sample_size is the source of truth.
    const totalObservations =
        distribution?.sample_size ??
        distributionItems.reduce(
            (total, item) =>
                total + Number(item.count || 0),
            0
        );

    const dominantItem =
        distributionItems.length > 0
            ? distributionItems[0]
            : null;

    // Items that clear both a minimum sample size AND a meaningful lift
    // vs. the whole-card-pool baseline -- see getNotableDistributionItems
    // in chartUtils for why both conditions matter (a big % on a tiny n
    // is noise, not a finding).
    const notableItems = getNotableDistributionItems(
        distributionItems,
        totalObservations
    );
    const notableValues = new Set(
        notableItems.map((item) => item.value)
    );

    const associationWarning = association
        ? getAssociationReliabilityWarning(association)
        : null;

    const chartData =
        distribution && selectedPreset
            ? {
                ...createDistributionDataset(
                    distribution.distribution,
                    selectedPreset.target,
                    { includeBaseline: true }
                ),
                datasets:
                    createDistributionDataset(
                        distribution.distribution,
                        selectedPreset.target,
                        { includeBaseline: true }
                    ).datasets.map(
                        (dataset, index) =>
                            index === 0
                                ? {
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
                                }
                                : dataset
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
                        <span className="statistics-eyebrow">DIGITAL WORLD DATABASE</span>
                        <h1>ADVANCED STATISTICS</h1>
                        <p>Explore conditional distributions across the card database.</p>
                    </div>

                    <button
                        type="button"
                        className="digi-menu-button"
                        onClick={onClose}
                    >
                        BACK TO HOME
                    </button>
                </div>

                <section className="advanced-statistics-menu">
                    <div className="statistics-section-header">
                        <div>
                            <span>ANALYSIS MODULE</span>
                            <h2>BUILD ANALYSIS</h2>
                        </div>
                        <span>{fieldOptions.length} FIELDS</span>
                    </div>

                    <div className="distribution-pair-builder">
                        <div className="pair-field">
                            <label htmlFor="given-field-select">GIVEN</label>
                            <select
                                id="given-field-select"
                                value={givenField}
                                onChange={(event) => setGivenField(event.target.value)}
                            >
                                <option value="">SELECT FIELD...</option>
                                {fieldOptions.map((field) => (
                                    <option key={field} value={field} disabled={field === targetField}>
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
                            <label htmlFor="target-field-select">TARGET</label>
                            <select
                                id="target-field-select"
                                value={targetField}
                                onChange={(event) => setTargetField(event.target.value)}
                            >
                                <option value="">SELECT FIELD...</option>
                                {fieldOptions.map((field) => (
                                    <option key={field} value={field} disabled={field === givenField}>
                                        {getFieldLabel(field)}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </section>

                {selectedPreset && (
                    <>
                        <section className="advanced-statistics-query">
                            <div className="query-header">
                                <div>
                                    <span>SELECTED ANALYSIS</span>
                                    <h2>{selectedPreset.label}</h2>
                                </div>

                                <button
                                    type="button"
                                    className="statistics-reset-button"
                                    onClick={resetAnalysis}
                                >
                                    RESET ANALYSIS
                                </button>
                            </div>

                            <p className="query-description">
                                {selectedPreset.description}
                            </p>

                            <div className="query-form">
                                <div className="query-field">
                                    <label htmlFor="statistics-value">
                                        {getFieldLabel(selectedPreset.given)}
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

                                                {dominantItem?.lift != null && (
                                                    <div className="statistics-metric">
                                                        <span>
                                                            VS. BASELINE
                                                        </span>

                                                        <strong
                                                            className={
                                                                dominantItem.lift >= 1.3
                                                                    ? 'lift-up'
                                                                    : dominantItem.lift <= 0.7
                                                                        ? 'lift-down'
                                                                        : ''
                                                            }
                                                        >
                                                            {dominantItem.lift.toFixed(2)}x
                                                        </strong>
                                                    </div>
                                                )}
                                            </section>

                                            {association && (
                                                <section
                                                    className={`statistics-association ${
                                                        association.reliable === false
                                                            ? 'unreliable'
                                                            : 'reliable'
                                                    }`}
                                                >
                                                    <div className="statistics-association-header">
                                                        <span>
                                                            FIELD-LEVEL ASSOCIATION
                                                        </span>

                                                        <h3>
                                                            {getFieldLabel(selectedPreset.given)}
                                                            {' × '}
                                                            {getFieldLabel(selectedPreset.target)}
                                                        </h3>
                                                    </div>

                                                    <p className="statistics-association-body">
                                                        Cramér's V across the
                                                        {' '}
                                                        <strong>{association.sample_size ?? '—'}</strong>
                                                        {' '}
                                                        value pairs in the full dataset:
                                                        {' '}
                                                        <strong>
                                                            {Number(association.cramers_v).toFixed(3)}
                                                        </strong>
                                                        {' '}
                                                        (0 = no relationship, 1 = perfect).
                                                    </p>

                                                    {associationWarning && (
                                                        <p className="statistics-association-warning">
                                                            {associationWarning}
                                                        </p>
                                                    )}
                                                </section>
                                            )}

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

                                                                        {notableValues.has(item.value) && (
                                                                            <span
                                                                                className={
                                                                                    item.lift >= 1
                                                                                        ? 'distribution-lift-badge lift-up'
                                                                                        : 'distribution-lift-badge lift-down'
                                                                                }
                                                                                title="Meaningfully different from the full-dataset baseline"
                                                                            >
                                                                                {item.lift >= 1 ? '▲' : '▼'}
                                                                                {' '}
                                                                                {item.lift.toFixed(1)}x
                                                                            </span>
                                                                        )}
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