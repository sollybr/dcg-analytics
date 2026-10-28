import { useEffect, useRef, useState } from 'react';

const EDGE_ZONE = 40;       // px from the left edge where an open-swipe may start
const LOCK_THRESHOLD = 8;   // px of movement before deciding horizontal vs vertical
const OPEN_SNAP = 0.35;     // drag past 35% -> open
const CLOSE_SNAP = 0.65;    // drag below 65% -> close

export function useIsMobile(query = '(max-width: 700px)') {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches
  );

  useEffect(() => {
    const mq = window.matchMedia(query);
    const handler = (e) => setMatches(e.matches);
    setMatches(mq.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

export default function DashboardDrawer({
  open,
  enabled,
  onOpen,
  onClose,
  items,
  activeId,
}) {
  const drawerRef = useRef(null);
  const backdropRef = useRef(null);
  const openRef = useRef(open);
  openRef.current = open;

  // Swipe gestures: edge-swipe right to open, swipe left to close.
  // The drawer follows the finger, then snaps open/closed on release.
  useEffect(() => {
    if (!enabled) return;

    const g = { mode: null, startX: 0, startY: 0, locked: false, progress: 0 };

    const clamp = (v) => Math.max(0, Math.min(1, v));

    const apply = (p) => {
      const drawer = drawerRef.current;
      const backdrop = backdropRef.current;
      if (!drawer || !backdrop) return;
      drawer.style.visibility = 'visible';
      drawer.style.transition = 'none';
      drawer.style.transform = `translateX(${(p - 1) * 100}%)`;
      backdrop.style.visibility = 'visible';
      backdrop.style.transition = 'none';
      backdrop.style.opacity = String(p);
    };

    const reset = () => {
      [drawerRef.current, backdropRef.current].forEach((el) => {
        if (!el) return;
        el.style.visibility = '';
        el.style.transition = '';
        el.style.transform = '';
        el.style.opacity = '';
      });
    };

    const onTouchStart = (e) => {
      if (e.touches.length !== 1) {
        g.mode = null;
        return;
      }
      const t = e.touches[0];
      g.startX = t.clientX;
      g.startY = t.clientY;
      g.locked = false;
      g.progress = openRef.current ? 1 : 0;

      if (openRef.current) g.mode = 'close';
      else if (t.clientX <= EDGE_ZONE) g.mode = 'open';
      else g.mode = null;
    };

    const onTouchMove = (e) => {
      if (!g.mode) return;
      const t = e.touches[0];
      const dx = t.clientX - g.startX;
      const dy = t.clientY - g.startY;

      if (!g.locked) {
        if (Math.abs(dy) > LOCK_THRESHOLD && Math.abs(dy) > Math.abs(dx)) {
          g.mode = null; // vertical scroll, not ours
          return;
        }
        if (Math.abs(dx) > LOCK_THRESHOLD && Math.abs(dx) > Math.abs(dy)) {
          const right = g.mode === 'open' && dx > 0;
          const left = g.mode === 'close' && dx < 0;
          if (right || left) g.locked = true;
          else g.mode = null;
        }
        if (!g.locked) return;
      }

      const w = drawerRef.current?.offsetWidth || 280;
      g.progress = clamp(g.mode === 'open' ? dx / w : 1 + dx / w);
      apply(g.progress);
    };

    const onTouchEnd = () => {
      if (g.mode && g.locked) {
        const shouldOpen =
          g.mode === 'open' ? g.progress > OPEN_SNAP : g.progress >= CLOSE_SNAP;
        reset(); // hand control back to the CSS class so it animates the snap
        if (shouldOpen) onOpen();
        else onClose();
      }
      g.mode = null;
      g.locked = false;
    };

    document.addEventListener('touchstart', onTouchStart, { passive: true });
    document.addEventListener('touchmove', onTouchMove, { passive: true });
    document.addEventListener('touchend', onTouchEnd);
    document.addEventListener('touchcancel', onTouchEnd);

    return () => {
      document.removeEventListener('touchstart', onTouchStart);
      document.removeEventListener('touchmove', onTouchMove);
      document.removeEventListener('touchend', onTouchEnd);
      document.removeEventListener('touchcancel', onTouchEnd);
    };
  }, [enabled, onOpen, onClose]);

  // Escape closes; page behind doesn't scroll while the drawer is open.
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  return (
    <>
      <div
        ref={backdropRef}
        className={`digi-drawer-backdrop${open ? ' open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        ref={drawerRef}
        className={`digi-drawer${open ? ' open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        aria-hidden={!open}
      >
        <div className="digi-drawer-header">
          <span className="digi-drawer-title">MENU</span>
          <button
            type="button"
            className="digi-drawer-close"
            onClick={onClose}
            aria-label="Close menu"
          >
            ✕
          </button>
        </div>

        <nav className="digi-drawer-nav">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`digi-drawer-item${activeId === item.id ? ' active' : ''}`}
              onClick={item.onClick}
              tabIndex={open ? 0 : -1}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
}
