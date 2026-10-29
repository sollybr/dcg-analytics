import { lazy, Suspense, useState, useEffect, useRef, useCallback, useMemo } from 'react';
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

import {
  Bar,
  Pie,
  Doughnut,
} from 'react-chartjs-2';

import {
  getColors,
} from './cardUtils';

import {
  DISTINCT_COLORS_15,
  createInteractiveDatasets,
  createExpansionTypeDatasets,
  stackedDarkOptions,
} from './chartUtils';

import { fetchAnalytics, fetchCardsByName, fetchCardsByType } from './api';
import { createDiagonalPattern } from './stripedPattern';

const AnalyticsChart = lazy(() => import('./components/AnalyticsChart'));
import DashboardHeader from './components/DashboardHeader';
import DashboardFooter from './components/DashboardFooter';
import DashboardDrawer, { useIsMobile } from './components/DashboardDrawer';
const CardDetailView = lazy(() => import('./components/CardDetailView'));
const CardTypeDetailView = lazy(() => import('./components/CardTypeDetailView'));
const AdvancedStatisticsView = lazy(() => import('./components/AdvancedStatisticsView'));

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
ChartJS.defaults.font.family =
  "'Pixel Digivolve', monospace";

const ANALYTICS_EXCLUSIONS = { excludeExpansions: ['P', 'ST'], excludeTypes: ['Lesser'] };

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [activeScreen, setActiveScreen] = useState('home');

  const [selectedCardName, setSelectedCardName] =
    useState(null);

  const [selectedCards, setSelectedCards] = useState([]);
  const [cardsLoading, setCardsLoading] =
    useState(false);
  const [cardsError, setCardsError] = useState(null);

  const [selectedType, setSelectedType] = useState(null);
  const [typeCards, setTypeCards] = useState([]);
  const [typePage, setTypePage] = useState(1);
  const [hasMoreType, setHasMoreType] = useState(true);
  const [typeCardsLoading, setTypeCardsLoading] = useState(false);
  const observerTarget = useRef(null);

  const isMobile = useIsMobile();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const openDrawer = useCallback(() => setDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  useEffect(() => {
    if (!isMobile) setDrawerOpen(false);
  }, [isMobile]);

  useEffect(() => {
    fetchAnalytics(ANALYTICS_EXCLUSIONS)
      .then((result) => { setData(result); setLoading(false); })
      .catch((error) => {
        console.error('Error fetching analytics:', error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedType) return;

    const loadTypeCards = async () => {
      setTypeCardsLoading(true);

      try {
        console.log('Fetching:', selectedType, typePage);

        const data = await fetchCardsByType(
          selectedType,
          typePage
        );

        console.log('Response:', data);

        setTypeCards((prevCards) => [
          ...prevCards,
          ...data.cards,
        ]);

        if (typePage >= data.total_pages) {
          setHasMoreType(false);
        }
      } catch (error) {
        console.error('fetchCardsByType failed:', error);
      } finally {
        setTypeCardsLoading(false);
      }
    };

    loadTypeCards();
  }, [selectedType, typePage]);

  useEffect(() => {
    if (
      !selectedType ||
      !observerTarget.current ||
      !hasMoreType ||
      typeCardsLoading
    ) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        console.log(
          'Observer:',
          entries[0].isIntersecting,
          'hasMore:',
          hasMoreType,
          'loading:',
          typeCardsLoading
        );

        if (entries[0].isIntersecting) {
          setTypePage((prevPage) => prevPage + 1);
        }
      },
      {
        threshold: 0.1,
      }
    );

    observer.observe(observerTarget.current);

    return () => {
      observer.disconnect();
    };
  }, [
    selectedType,
    hasMoreType,
    typeCardsLoading,
    typeCards,
  ]);

  const openCardName = async (name) => {
    setSelectedCardName(name);
    setSelectedCards([]);
    setCardsError(null);
    setCardsLoading(true);

    try {
      const result = await fetchCardsByName(name);

      setSelectedCards(
        Array.isArray(result.cards)
          ? result.cards
          : []
      );
    } catch (error) {
      console.error(
        'Error fetching cards:',
        error
      );

      setCardsError(error.message);
    } finally {
      setCardsLoading(false);
    }
  };

  const closeCardName = () => {
    setSelectedCardName(null);
    setSelectedCards([]);
    setCardsError(null);
  };

  const closeCardType = () => {
    setSelectedType(null);
    setTypeCards([]);
    setTypePage(1);
    setHasMoreType(true);
  };

  const goHome = () => {
    closeCardName();
    closeCardType();
    setActiveScreen('home');
    setDrawerOpen(false);
  };

  const goAdvanced = () => {
    closeCardName();
    closeCardType();
    setActiveScreen('advanced');
    setDrawerOpen(false);
  };

  const nameChartData = useMemo(() => {
    const labels = data?.name_labels || [];
    const datasets = createInteractiveDatasets(
      labels,
      data?.name_data,
      DISTINCT_COLORS_15
    ).map((ds) => {
      const colors = Object.keys(data?.name_colors?.[ds.label] || {});
      if (!colors.length) return ds; // fall back to the solid color
      return {
        ...ds,
        backgroundColor: createDiagonalPattern(getColors(colors)),
      };
    });
    return { labels, datasets };
  }, [data]);

  if (loading || !data) {
    return (
      <div className="digi-loading-container">
        <div className="digi-spinner-wrapper">
          <div className="digi-spinner"></div>
          <img
            src="https://raw.githubusercontent.com/sollybr/sollybr/tenet/assets/gabumon.png"
            alt="Loading Favicon"
            className="digi-spinner-favicon"
          />
        </div>
        <p className="digi-loading-text">
          CONNECTING TO DIGITAL WORLD DATABASE...
        </p>
      </div>
    );
  }

  let content;

  if (selectedCardName) {
    content = (
      <CardDetailView
        selectedCardName={selectedCardName}
        selectedCards={selectedCards}
        cardsLoading={cardsLoading}
        cardsError={cardsError}
      />
    );
  } else if (selectedType) {
    content = (
      <CardTypeDetailView
        selectedType={selectedType}
        typeCards={typeCards}
        cardsLoading={typeCardsLoading}
        cardsError={null}
        hasMoreType={hasMoreType}
        observerTarget={observerTarget}
      />
    );
  } else if (activeScreen === 'advanced') {
    content = <AdvancedStatisticsView />;
  } else {
    content = (
      <div className="digi-grid">
        <AnalyticsChart title="CARD DISTRIBUTION">
          <Pie
            data={{
              labels: data.type_labels || [],
              datasets: [
                {
                  data: data.type_data || [],
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
        </AnalyticsChart>

        <AnalyticsChart title="TOP 15 ORIGINAL CARD PRINTED NAMES">
          <Bar
            data={nameChartData}
            options={{
              ...stackedDarkOptions,
              plugins: {
                ...stackedDarkOptions.plugins,
                tooltip: {
                  callbacks: {
                    label: (ctx) => `${ctx.dataset.label} total: ${ctx.parsed.y}`,
                    afterLabel: (ctx) =>
                      Object.entries(data.name_colors?.[ctx.dataset.label] ?? {}).map(
                        ([color, count]) => `${color}: ${count}`
                      ),
                  },
                },
              },
              onClick: (_event, elements) => {
                if (!elements?.length) return;
                const name = data.name_labels?.[elements[0].index];
                if (name) openCardName(name);
              },
              onHover: (event, elements) => {
                if (event?.native?.target) {
                  event.native.target.style.cursor = elements?.length ? 'pointer' : 'default';
                }
              },
            }}
          />
        </AnalyticsChart>

        <AnalyticsChart title="GENERAL COLOR SPECTRUM">
          <Doughnut
            data={{
              labels:
                data.single_color_labels || [],
              datasets: [
                {
                  data:
                    data.single_color_data || [],
                  backgroundColor: getColors(
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
        </AnalyticsChart>

        <AnalyticsChart title="TOP 10 MULTICOLOR">
          <Bar
            data={{
              labels:
                data.multicolor_labels || [],
              datasets: createInteractiveDatasets(
                data.multicolor_labels,
                data.multicolor_data,
                getColors
              ),
            }}
            options={{
              ...stackedDarkOptions,
              indexAxis: 'y',
            }}
          />
        </AnalyticsChart>

        <AnalyticsChart title="TOP 20 CARD TYPES">
          <Bar
            data={{
              labels:
                data.subtype_labels || [],
              datasets: createInteractiveDatasets(
                data.subtype_labels,
                data.subtype_data,
                DISTINCT_COLORS_15
              ),
            }}
            options={{
              ...stackedDarkOptions,
              onClick: (event, elements, chart) => {
                console.log('Chart clicked:', elements);

                if (elements.length > 0) {
                  const dataIndex = elements[0].index;
                  const clickedType = chart.data.labels?.[dataIndex];

                  console.log('Clicked type:', clickedType);

                  if (!clickedType) return;

                  setSelectedType(clickedType);
                  setTypeCards([]);
                  setTypePage(1);
                  setHasMoreType(true);
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
        </AnalyticsChart>

        <AnalyticsChart title="EXPANSIONS DISTRIBUTION">
          <Bar
            data={{
              labels:
                data.expansion_labels || [],
              datasets: createExpansionTypeDatasets(
                data.expansion_labels,
                data.expansion_data,
                data.expansion_types
              ),
            }}
            options={stackedDarkOptions}
          />
        </AnalyticsChart>

        <AnalyticsChart title="SECRET RARE (SEC) SPECTRUM">
          <Pie
            data={{
              labels:
                data.sec_color_labels || [],
              datasets: [
                {
                  data:
                    data.sec_color_data || [],
                  backgroundColor: getColors(
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
        </AnalyticsChart>
      </div>
    );
  }

  return (
    <div className="digi-dashboard">
      <div className="digi-topbar">
        <button
          type="button"
          className="digi-menu-toggle"
          onClick={openDrawer}
          aria-label="Open menu"
          aria-expanded={drawerOpen}
        >
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <path
              d="M3 6h18M3 12h18M3 18h18"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
        </button>
        <DashboardHeader totalCards={data.total_cards} />
      </div>

      <div className="digi-dashboard-menu">
        <button
          type="button"
          className={`digi-menu-button${activeScreen === 'home' ? ' active' : ''}`}
          onClick={goHome}
        >
          HOME
        </button>

        <button
          type="button"
          className={`digi-menu-button${activeScreen === 'advanced' ? ' active' : ''}`}
          onClick={goAdvanced}
        >
          MORE DISTRIBUTIONS
        </button>
      </div>

      <Suspense
        fallback={
          <div className="digi-loading-container">
            <div className="digi-spinner-wrapper">
              <div className="digi-spinner"></div>
              <img
                src="https://raw.githubusercontent.com/sollybr/sollybr/tenet/assets/gabumon.png"
                alt="Loading Favicon"
                className="digi-spinner-favicon"
              />
            </div>
            <p className="digi-loading-text">LOADING MODULE...</p>
          </div>
        }
      >
        {content}
      </Suspense>

      <DashboardFooter />

      <DashboardDrawer
        open={drawerOpen}
        enabled={isMobile}
        onOpen={openDrawer}
        onClose={closeDrawer}
        activeId={activeScreen}
        items={[
          { id: 'home', label: 'HOME', onClick: goHome },
          { id: 'advanced', label: 'MORE DISTRIBUTIONS', onClick: goAdvanced },
        ]}
      />
    </div>
  );

}