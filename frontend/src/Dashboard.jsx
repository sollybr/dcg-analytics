
import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Doughnut } from 'react-chartjs-2';

import {
  COLOR_MAP,
  getCardColors,
  getCardExpansion,
  getCardTypes,
  getCardLevel,
} from './cardUtils';

import './Dashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

ChartJS.defaults.color = '#7dd3fc';
ChartJS.defaults.font.family = "'Pixel Digivolve', monospace";

const getColors = (colors = []) => {
  if (!Array.isArray(colors)) {
    return [];
  }

  return colors.map((label) => {
    if (COLOR_MAP[label]) {
      return COLOR_MAP[label];
    }

    if (
      typeof label === 'string' &&
      label.includes('/')
    ) {
      const primary = label
        .split('/')[0]
        .trim();

      return (
        COLOR_MAP[primary] ||
        COLOR_MAP.Unknown
      );
    }

    return COLOR_MAP.Unknown;
  });
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [selectedCardName, setSelectedCardName] =
    useState(null);

  const [selectedCards, setSelectedCards] =
    useState([]);

  const [cardsLoading, setCardsLoading] =
    useState(false);

  const [cardsError, setCardsError] =
    useState(null);

  useEffect(() => {
    fetch('/api/analytics/')
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Analytics API returned ${response.status}`
          );
        }

        return response.json();
      })
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((error) => {
        console.error(
          'Error fetching analytics:',
          error
        );

        setLoading(false);
      });
  }, []);

  const openCardName = (name) => {
    setSelectedCardName(name);
    setSelectedCards([]);
    setCardsError(null);
    setCardsLoading(true);

    const encodedName =
      encodeURIComponent(name);

    fetch(
      `/api/cards/?name=${encodedName}`
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Cards API returned ${response.status}`
          );
        }

        return response.json();
      })
      .then((result) => {
        setSelectedCards(
          Array.isArray(result.cards)
            ? result.cards
            : []
        );
        setCardsLoading(false);
      })
      .catch((error) => {
        console.error(
          'Error fetching cards:',
          error
        );

        setCardsError(error.message);
        setCardsLoading(false);
      });
  };

  const closeCardName = () => {
    setSelectedCardName(null);
    setSelectedCards([]);
    setCardsError(null);
  };

  if (loading || !data) {
    return (
      <div className="digi-loader">
        <div className="digi-spinner"></div>
        <p className="digi-loading-text">
          CONNECTING TO DIGITAL WORLD DATABASE...
        </p>
      </div>
    );
  }

  const darkOptions = {
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

  /*
   * DETAIL PAGE
   */
  if (selectedCardName) {
    return (
      <div className="digi-dashboard">
        <header className="digi-header">
          <div className="digi-logo">
            DIGIMON ANALYTICS OS
          </div>

          <div className="digi-status">
            <span className="indicator"></span>
            <span>SYSTEM ONLINE</span>

            <span style={{ opacity: 0.4 }}>
              |
            </span>

            <span>
              CARDS INDEXED:{' '}
              {data.total_cards || 0}
            </span>
          </div>
        </header>

        <main className="digi-detail-view">
          <div className="digi-detail-header">
            <button
              className="digi-back-btn"
              onClick={closeCardName}
            >
              &larr; BACK TO DASHBOARD
            </button>

            <h2>
              CARDS NAMED:{' '}
              <span
                style={{
                  color: '#00f3ff',
                }}
              >
                {selectedCardName}
              </span>
            </h2>

            {!cardsLoading && !cardsError && (
              <p>
                {selectedCards.length}{' '}
                UNIQUE CARDS FOUND
              </p>
            )}
          </div>

          {cardsLoading && (
            <div className="digi-loader">
              <div className="digi-spinner"></div>

              <p className="digi-loading-text">
                LOADING CARD DATA...
              </p>
            </div>
          )}

          {cardsError && (
            <div className="digi-error-container">
              <h2>
                CARD DATABASE OFFLINE
              </h2>

              <p>{cardsError}</p>
            </div>
          )}

          {!cardsLoading &&
            !cardsError &&
            selectedCards.length === 0 && (
              <div className="digi-error-container">
                <h2>NO CARDS FOUND</h2>

                <p>
                  No cards were returned for this
                  name.
                </p>
              </div>
            )}

          {!cardsLoading &&
            !cardsError &&
            selectedCards.length > 0 && (
              <div className="digi-card-grid">
                {selectedCards.map(
                  (card, index) => {
                    const cardId =
                      card.cardNumber ||
                      card.id ||
                      `card-${index}`;

                    const colors =
                      getCardColors(
                        card.color ||
                          card.colors
                      );

                    const level =
                      getCardLevel(card);

                    const types =
                      getCardTypes(card);

                    return (
                      <div
                        key={`${cardId}-${index}`}
                        className="digi-card-item"
                      >
                        <div className="card-header">
                          <span className="card-id">
                            {cardId}
                          </span>

                          <span className="card-rarity">
                            {card.rarity ||
                              'N/A'}
                          </span>
                        </div>

                        <h3 className="card-name">
                          {card.name?.english ||
                            selectedCardName}
                        </h3>

                        <div className="card-details">
                          <p>
                            <strong>
                              EXPANSION:
                            </strong>{' '}
                            {getCardExpansion(
                              card
                            )}
                          </p>

                          <p>
                            <strong>
                              COLOR:
                            </strong>{' '}
                            {colors.join(
                              ' / '
                            )}
                          </p>

                          <p>
                            <strong>
                              CARD TYPE:
                            </strong>{' '}
                            {card.cardType ||
                              'N/A'}
                          </p>

                          {types.length > 0 && (
                            <p>
                              <strong>
                                TYPE:
                              </strong>{' '}
                              {types.join(
                                ' / '
                              )}
                            </p>
                          )}

                          {level !== null && (
                            <p>
                              <strong>
                                LEVEL:
                              </strong>{' '}
                              Lv.{level}
                            </p>
                          )}

                          {card.playCost !==
                            undefined &&
                            card.playCost !==
                              null &&
                            card.playCost !==
                              '-' && (
                              <p>
                                <strong>
                                  PLAY COST:
                                </strong>{' '}
                                {card.playCost}
                              </p>
                            )}

                          {card.dp &&
                            card.dp !== '-' && (
                              <p>
                                <strong>
                                  DP:
                                </strong>{' '}
                                {card.dp}
                              </p>
                            )}

                          {card.form &&
                            card.form !== '-' && (
                              <p>
                                <strong>
                                  FORM:
                                </strong>{' '}
                                {card.form}
                              </p>
                            )}

                          {card.attribute &&
                            card.attribute !==
                              '-' && (
                              <p>
                                <strong>
                                  ATTRIBUTE:
                                </strong>{' '}
                                {card.attribute}
                              </p>
                            )}
                        </div>

                        {card.effect &&
                          card.effect !== '-' && (
                            <div className="card-effect">
                              <strong>
                                EFFECT
                              </strong>

                              <p>
                                {card.effect}
                              </p>
                            </div>
                          )}

                        {card.digivolveEffect &&
                          card.digivolveEffect !==
                            '-' && (
                            <div className="card-effect">
                              <strong>
                                DIGIVOLUTION EFFECT
                              </strong>

                              <p>
                                {
                                  card.digivolveEffect
                                }
                              </p>
                            </div>
                          )}

                        {card.securityEffect &&
                          card.securityEffect !==
                            '-' && (
                            <div className="card-effect">
                              <strong>
                                SECURITY EFFECT
                              </strong>

                              <p>
                                {
                                  card.securityEffect
                                }
                              </p>
                            </div>
                          )}
                      </div>
                    );
                  }
                )}
              </div>
            )}
        </main>

        <footer className="digi-footer">
          <div className="footer-content">
            <div className="footer-section">
              <h3>
                DIGIMON ANALYTICS OS
              </h3>

              <p>
                An open-source card statistics
                and telemetry portal built with
                React and Django.
              </p>

              <p>
                Source code licensed under the{' '}
                <strong>MIT License</strong>.
              </p>
            </div>

            <div className="footer-section">
              <h3>DATA SOURCES</h3>

              <ul className="footer-links">
                <li>
                  Dataset provided by{' '}
                  <a
                    href="https://github.com/TakaOtaku/Digimon-Card-App"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    TakaOtaku/Digimon-Card-App
                  </a>
                </li>

                <li>
                  Official Digimon Card Game:{' '}
                  <a
                    href="https://world.digimoncard.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    world.digimoncard.com
                  </a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h3>LEGAL DISCLAIMER</h3>

              <p>
                This application is an unofficial,
                non-commercial fan project. All
                card artwork, names, and trademarks
                belong to{' '}
                <strong>
                  Bandai Namco Entertainment
                </strong>
                ,{' '}
                <strong>Toei Animation</strong>,
                and{' '}
                <strong>
                  WiZ/Shueisha
                </strong>
                .
              </p>
            </div>
          </div>

          <div className="footer-bottom">
            &copy;{' '}
            {new Date().getFullYear()}{' '}
            DIGIMON ANALYTICS OS. NOT AFFILIATED
            WITH OR ENDORSED BY BANDAI NAMCO.
          </div>
        </footer>
      </div>
    );
  }

  /*
   * DASHBOARD
   */
  return (
    <div className="digi-dashboard">
      <header className="digi-header">
        <div className="digi-logo">
          DIGIMON ANALYTICS OS
        </div>

        <div className="digi-status">
          <span className="indicator"></span>
          <span>SYSTEM ONLINE</span>

          <span style={{ opacity: 0.4 }}>
            |
          </span>

          <span>
            CARDS INDEXED:{' '}
            {data.total_cards || 0}
          </span>
        </div>
      </header>

      <div className="digi-grid">
        <div className="digi-card">
          <div className="card-header">
            CARD TYPES
          </div>

          <div className="chart-container">
            <Pie
              data={{
                labels:
                  data.type_labels || [],

                datasets: [
                  {
                    data:
                      data.type_data || [],

                    backgroundColor: [
                      '#00f3ff',
                      '#ff6600',
                      '#a855f7',
                      '#22c55e',
                    ],
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
              }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            TOP 15 PRINTED NAMES
          </div>

          <div className="chart-container">
            <Bar
              data={{
                labels:
                  data.name_labels || [],

                datasets: [
                  {
                    label: 'Count',
                    data:
                      data.name_data || [],
                    backgroundColor:
                      '#ff6600',
                  },
                ],
              }}
              options={{
                ...darkOptions,

                onClick: (
                  event,
                  elements
                ) => {
                  if (
                    !elements ||
                    elements.length === 0
                  ) {
                    return;
                  }

                  const index =
                    elements[0].index;

                  const name =
                    data.name_labels?.[
                      index
                    ];

                  if (name) {
                    openCardName(name);
                  }
                },

                onHover: (
                  event,
                  elements
                ) => {
                  if (event?.native?.target) {
                    event.native.target.style.cursor =
                      elements?.length
                        ? 'pointer'
                        : 'default';
                  }
                },
              }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            SINGLE COLOR SPECTRUM
          </div>

          <div className="chart-container">
            <Doughnut
              data={{
                labels:
                  data.single_color_labels ||
                  [],

                datasets: [
                  {
                    data:
                      data.single_color_data ||
                      [],

                    backgroundColor:
                      getColors(
                        data.single_color_labels
                      ),
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
              }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            TOP 10 MULTICOLOR HYBRIDS
          </div>

          <div className="chart-container">
            <Bar
              data={{
                labels:
                  data.multicolor_labels ||
                  [],

                datasets: [
                  {
                    label: 'Count',
                    data:
                      data.multicolor_data ||
                      [],

                    backgroundColor:
                      getColors(
                        data.multicolor_labels
                      ),
                  },
                ],
              }}
              options={{
                ...darkOptions,
                indexAxis: 'y',
              }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            TOP 20 SUBTYPES & TRAITS
          </div>

          <div className="chart-container">
            <Bar
              data={{
                labels:
                  data.subtype_labels ||
                  [],

                datasets: [
                  {
                    label: 'Count',
                    data:
                      data.subtype_data ||
                      [],

                    backgroundColor:
                      '#00f3ff',
                  },
                ],
              }}
              options={darkOptions}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            EXPANSIONS DISTRIBUTION
          </div>

          <div className="chart-container">
            <Bar
              data={{
                labels:
                  data.expansion_labels ||
                  [],

                datasets: [
                  {
                    label: 'Cards',
                    data:
                      data.expansion_data ||
                      [],

                    backgroundColor:
                      '#38bdf8',
                  },
                ],
              }}
              options={darkOptions}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">
            SECRET RARE (SEC) SPECTRUM
          </div>

          <div className="chart-container">
            <Pie
              data={{
                labels:
                  data.sec_color_labels ||
                  [],

                datasets: [
                  {
                    data:
                      data.sec_color_data ||
                      [],

                    backgroundColor:
                      getColors(
                        data.sec_color_labels
                      ),
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
              }}
            />
          </div>
        </div>
      </div>

      <footer className="digi-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>
              DIGIMON ANALYTICS OS
            </h3>

            <p>
              An open-source card statistics
              and telemetry portal built with
              React and Django.
            </p>

            <p>
              Source code licensed under the{' '}
              <strong>MIT License</strong>.
            </p>
          </div>

          <div className="footer-section">
            <h3>DATA SOURCES</h3>

            <ul className="footer-links">
              <li>
                Dataset provided by{' '}
                <a
                  href="https://github.com/TakaOtaku/Digimon-Card-App"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  TakaOtaku/Digimon-Card-App
                </a>
              </li>

              <li>
                Official Digimon Card Game:{' '}
                <a
                  href="https://world.digimoncard.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  world.digimoncard.com
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h3>LEGAL DISCLAIMER</h3>

            <p>
              This application is an unofficial,
              non-commercial fan project. All
              card artwork, names, and trademarks
              belong to{' '}
              <strong>
                Bandai Namco Entertainment
              </strong>
              ,{' '}
              <strong>Toei Animation</strong>,
              and{' '}
              <strong>WiZ/Shueisha</strong>.
            </p>
          </div>
        </div>

        <div className="footer-bottom">
          &copy;{' '}
          {new Date().getFullYear()}{' '}
          DIGIMON ANALYTICS OS. NOT AFFILIATED
          WITH OR ENDORSED BY BANDAI NAMCO.
        </div>
      </footer>
    </div>
  );
}
