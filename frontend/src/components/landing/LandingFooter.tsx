import { Brand } from '../ui/Brand';

export function LandingFooter() {
  return (
    <footer className="marketing-footer-wrap">
      <div className="wrap marketing-footer">
        <Brand size="sm" />
        <div className="footer-links">
          <a href="#product">Product</a>
          <a href="#how">How it works</a>
          <a href="#principles">Principles</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            Swagger API
          </a>
        </div>
        <div className="footer-copy">
          <span>© 2026 ChangeRadar. Software Change Impact Intelligence.</span>
          <span className="footer-version">v0.1.1 ENTERPRISE FOUNDATION</span>
        </div>
      </div>
    </footer>
  );
}
