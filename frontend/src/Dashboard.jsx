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
import { useState, useEffect, useRef } from 'react';

import AnalyticsChart from './components/AnalyticsChart';
import DashboardHeader from './components/DashboardHeader';
import DashboardFooter from './components/DashboardFooter';
import CardDetailView from './components/CardDetailView';
import CardTypeDetailView from './components/CardTypeDetailView';
import AdvancedStatisticsView from './components/AdvancedStatisticsView';

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
  const [typeTotalCards, setTypeTotalCards] = useState(0);
  const observerTarget = useRef(null);

  useEffect(() => {
    fetchAnalytics({ excludeExpansions: ['P', 'ST'], excludeTypes: ['Lesser'] })
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

        setTypeTotalCards(data.total_count);

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
    setTypeTotalCards(0);
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

  if (selectedCardName) {
    return (
      <CardDetailView
      selectedCardName={selectedCardName}
      selectedCards={selectedCards}
      cardsLoading={cardsLoading}
      cardsError={cardsError}
      totalCards={data.total_cards}
      onClose={closeCardName}
      />
      );
  }

  if (selectedType) {
    return (
      <CardTypeDetailView
      selectedType={selectedType}
      typeCards={typeCards}
      cardsLoading={typeCardsLoading}
      cardsError={null}
      totalCards={typeTotalCards}
      hasMoreType={hasMoreType}
      observerTarget={observerTarget}
      onClose={closeCardType}
      />
      );
  }

  if (activeScreen === 'advanced') {
      return (
          <AdvancedStatisticsView
              onClose={() => setActiveScreen('home')}
          />
      );
  }

  return (
    <div className="digi-dashboard">
    <DashboardHeader
    totalCards={data.total_cards}
    />
    <div className="digi-dashboard-menu">
        <button
            type="button"
            className="digi-menu-button active"
            onClick={() => setActiveScreen('home')}
        >
            HOME
        </button>

        <button
            type="button"
            className="digi-menu-button"
            onClick={() => setActiveScreen('advanced')}
        >
            MORE DISTRIBUTIONS
        </button>
    </div>
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
    data={{
      labels: data.name_labels || [],
      datasets: createInteractiveDatasets(
        data.name_labels,
        data.name_data,
        DISTINCT_COLORS_15
        ),
    }}
    options={{
      ...stackedDarkOptions,

      onClick: (_event, elements) => {
        if (
          !elements ||
          elements.length === 0
          ) {
          return;
      }

      const index = elements[0].index;
      const name =
      data.name_labels?.[index];

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

  <DashboardFooter />
  </div>
  );
}