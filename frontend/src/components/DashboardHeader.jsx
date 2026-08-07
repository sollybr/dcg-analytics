export default function DashboardHeader({ totalCards }) {
  return (
    <header className="digi-header">
      <div className="digi-logo">
        DIGIMON ANALYTICS OS
      </div>

      <div className="digi-status">
        <span className="indicator"></span>
        <span>SYSTEM ONLINE</span>
        <span style={{ opacity: 0.4 }}>|</span>
        <span>
          CARDS INDEXED: {totalCards || 0}
        </span>
      </div>
    </header>
  );
}