const cache = new Map();

/**
 * Seamless 45° stripe pattern with one equal-width stripe per color.
 * One color returns a plain solid color.
 */
export function createDiagonalPattern(colors, stripe = 10) {
  if (colors.length === 1) return colors[0];

  const key = `${stripe}|${colors.join('|')}`;
  if (cache.has(key)) return cache.get(key);

  const n = colors.length;
  const T = stripe * n;
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