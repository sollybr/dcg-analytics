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
      bgColor = colorStrategy[index % colorStrategy.length];
    } else if (typeof colorStrategy === 'string') {
      bgColor = colorStrategy;
    }

    return {
      label,
      data: labels.map((_, i) =>
        i === index ? dataArray[index] : null
      ),
      backgroundColor: bgColor,
    };
  });
};

export const darkOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#00f3ff',
        font: {
          family: "'Pixel Digivolve', monospace",
        },
      },
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#00f3ff',
        font: {
          family: "'Pixel Digivolve', monospace",
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
          family: "'Pixel Digivolve', monospace",
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