const cache = new Map();

/**
 * Seamless 45° stripe pattern with stripe widths proportional to their quantities.
 * Single color entry returns a plain solid color.
 */
export function createDiagonalPattern(colorEntries, targetWidth = 120) {
  if (colorEntries.length === 1) return colorEntries[0][0];

  const totalCount = colorEntries.reduce((sum, [, count]) => sum + count, 0);
  if (totalCount === 0) return colorEntries[0]?.[0] || '#ccc';

  const key = `${targetWidth}|${colorEntries.map(([c, cnt]) => `${c}:${cnt}`).join('|')}`;
  if (cache.has(key)) return cache.get(key);

  const T = targetWidth;
  const tile = document.createElement('canvas');
  tile.width = T;
  tile.height = T;
  const g = tile.getContext('2d');

  let currentX = 0;
  colorEntries.forEach(([color, count]) => {
    const proportion = count / totalCount;
    const stripeWidth = proportion * T;

    g.fillStyle = color;
    // Draw shifted copies so the slanted stripes wrap seamlessly.
    for (const off of [-T, 0, T]) {
      g.beginPath();
      g.moveTo(currentX + off, 0);
      g.lineTo(currentX + stripeWidth + off, 0);
      g.lineTo(currentX + stripeWidth + off - T, T);
      g.lineTo(currentX + off - T, T);
      g.closePath();
      g.fill();
    }
    currentX += stripeWidth;
  });

  const pattern = tile.getContext('2d').createPattern(tile, 'repeat');
  cache.set(key, pattern);
  return pattern;
}