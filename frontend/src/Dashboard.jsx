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
  stackedDarkOptions,
} from './chartUtils';

import {
  fetchAnalytics,
  fetchCardsByName,
} from './api';

import AnalyticsChart from './components/AnalyticsChart';
import CardDetailView from './components/CardDetailView';
import DashboardFooter from './components/DashboardFooter';
import DashboardHeader from './components/DashboardHeader';

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

  const [selectedCardName, setSelectedCardName] =
    useState(null);

  const [selectedCards, setSelectedCards] = useState([]);
  const [cardsLoading, setCardsLoading] =
    useState(false);
  const [cardsError, setCardsError] = useState(null);

  useEffect(() => {
    fetchAnalytics()
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

  return (
    <div className="digi-dashboard">
      <DashboardHeader
        totalCards={data.total_cards}
      />

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
            options={stackedDarkOptions}
          />
        </AnalyticsChart>

        <AnalyticsChart title="EXPANSIONS DISTRIBUTION">
          <Bar
            data={{
              labels:
                data.expansion_labels || [],
              datasets: createInteractiveDatasets(
                data.expansion_labels,
                data.expansion_data,
                DISTINCT_COLORS_15
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