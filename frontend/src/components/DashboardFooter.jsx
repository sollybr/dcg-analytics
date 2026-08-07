export default function DashboardFooter() {
  return (
    <footer className="digi-footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>DIGIMON ANALYTICS OS</h3>

          <p>
            An open-source card statistics and telemetry
            portal built with React and Django.
          </p>

          <p>
            Source code licensed under the{' '}
            <strong>MIT License</strong>.
          </p>
        </div>

        <div className="footer-section">
          <h3>DATA SOURCES</h3>

          <ul className="footer-links">
            <li>
              Dataset provided by{' '}
              <a
                href="https://github.com/TakaOtaku/Digimon-Card-App"
                target="_blank"
                rel="noopener noreferrer"
              >
                TakaOtaku/Digimon-Card-App
              </a>
            </li>

            <li>
              Official Digimon Card Game:{' '}
              <a
                href="https://world.digimoncard.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                world.digimoncard.com
              </a>
            </li>
          </ul>
        </div>

        <div className="footer-section">
          <h3>LEGAL DISCLAIMER</h3>

          <p>
            This application is an unofficial,
            non-commercial fan project. All card artwork,
            names, and trademarks belong to{' '}
            <strong>Bandai Namco Entertainment</strong>,{' '}
            <strong>Toei Animation</strong>, and{' '}
            <strong>WiZ/Shueisha</strong>.
          </p>
        </div>
      </div>

      <div className="footer-bottom">
        &copy; {new Date().getFullYear()} DIGIMON ANALYTICS OS.
        NOT AFFILIATED WITH OR ENDORSED BY BANDAI NAMCO.
      </div>
    </footer>
  );
}