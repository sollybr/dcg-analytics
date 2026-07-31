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

// Configure Chart.js global defaults with Pixel Digivolve
ChartJS.defaults.color = '#7dd3fc';
ChartJS.defaults.font.family = "'Pixel Digivolve', monospace";

const COLOR_MAP = {
  Red: '#ef4444',
  Blue: '#3b82f6',
  Yellow: '#eab308',
  Green: '#22c55e',
  Black: '#475569',
  Purple: '#a855f7',
  White: '#f8fafc',
  Unknown: '#64748b',
};

const getColors = (colors = []) => {
  if (!Array.isArray(colors)) return [];
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

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/analytics/')
      .then((response) => response.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  }, []);

  if (loading || !data) {
    return (
      <div className="digi-loader">
        <div className="digi-spinner"></div>
        {/* Italics applied to loader text */}
        <p className="digi-loading-text">CONNECTING TO DIGITAL WORLD DATABASE...</p>
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
          font: { family: "'Pixel Digivolve', monospace" }
        } 
      },
    },
    scales: {
      x: { 
        ticks: { color: '#00f3ff', font: { family: "'Pixel Digivolve', monospace" } }, 
        grid: { color: '#1e293b' } 
      },
      y: { 
        ticks: { color: '#00f3ff', font: { family: "'Pixel Digivolve', monospace" } }, 
        grid: { color: '#1e293b' } 
      },
    },
  };

  return (
    <div className="digi-dashboard">
      <header className="digi-header">
        <div className="digi-logo">DIGIMON ANALYTICS OS</div>
        <div className="digi-status">
          <span className="indicator"></span> SYSTEM ONLINE | CARDS INDEXED: {data.total_cards || 0}
        </div>
      </header>

      <div className="digi-grid">
        <div className="digi-card">
          <div className="card-header">CARD TYPES</div>
          <div className="chart-container">
            <Pie
              data={{
                labels: data.type_labels || [],
                datasets: [{ data: data.type_data || [], backgroundColor: ['#00f3ff', '#ff6600', '#a855f7', '#22c55e'] }],
              }}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">TOP 15 PRINTED NAMES</div>
          <div className="chart-container">
            <Bar
              data={{
                labels: data.name_labels || [],
                datasets: [{ label: 'Count', data: data.name_data || [], backgroundColor: '#ff6600' }],
              }}
              options={darkOptions}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">SINGLE COLOR SPECTRUM</div>
          <div className="chart-container">
            <Doughnut
              data={{
                labels: data.single_color_labels || [],
                datasets: [{ data: data.single_color_data || [], backgroundColor: getColors(data.single_color_labels) }],
              }}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">TOP 10 MULTICOLOR HYBRIDS</div>
          <div className="chart-container">
            <Bar
              data={{
                labels: data.multicolor_labels || [],
                datasets: [{ label: 'Count', data: data.multicolor_data || [], backgroundColor: getColors(data.multicolor_labels) }],
              }}
              options={{ ...darkOptions, indexAxis: 'y' }}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">TOP 20 SUBTYPES & TRAITS</div>
          <div className="chart-container">
            <Bar
              data={{
                labels: data.subtype_labels || [],
                datasets: [{ label: 'Count', data: data.subtype_data || [], backgroundColor: '#00f3ff' }],
              }}
              options={darkOptions}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">EXPANSIONS DISTRIBUTION</div>
          <div className="chart-container">
            <Bar
              data={{
                labels: data.expansion_labels || [],
                datasets: [{ label: 'Cards', data: data.expansion_data || [], backgroundColor: '#38bdf8' }],
              }}
              options={darkOptions}
            />
          </div>
        </div>

        <div className="digi-card">
          <div className="card-header">SECRET RARE (SEC) SPECTRUM</div>
          <div className="chart-container">
            <Pie
              data={{
                labels: data.sec_color_labels || [],
                datasets: [{ data: data.sec_color_data || [], backgroundColor: getColors(data.sec_color_labels) }],
              }}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}