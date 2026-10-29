const cache = new Map();

/**
 * Seamless 45° stripe pattern with one equal-width stripe per color.
 * One color returns a plain solid color.
 * Dynamically scales stripe widths to fit a target bar width (default 120px),
 * ensuring exactly n stripes are evenly distributed across the bar.
 */
export function createDiagonalPattern(colors, targetWidth = 120) {
  if (colors.length === 1) return colors[0];

  const n = colors.length;
  const stripe = targetWidth / n;
  const key = `${targetWidth}|${colors.join('|')}`;
  if (cache.has(key)) return cache.get(key);

  const T = targetWidth;
  const tile = document.createElement('canvas');
  tile.width = T;
  tile.height = T;
  const g = tile.getContext('2d');

  colors.forEach((color, i) => {
    g.fillStyle = color;
    // Draw shifted copies so the slanted stripes wrap seamlessly.
    for (const off of [-T, 0, T]) {
      g.beginPath();
      g.moveTo(i * stripe + off, 0);
      g.lineTo((i + 1) * stripe + off, 0);
      g.lineTo((i + 1) * stripe + off - T, T);
      g.lineTo(i * stripe + off - T, T);
      g.closePath();
      g.fill();
    }
  });

  const pattern = tile.getContext('2d').createPattern(tile, 'repeat');
  cache.set(key, pattern);
  return pattern;
}