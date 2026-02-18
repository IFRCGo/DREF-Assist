const IFRCFooter = () => {
  return (
    <footer className="mt-12 border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-5">
          <div>
            <h3 className="mb-3 text-sm font-bold font-heading text-foreground">ABOUT GO</h3>
            <p className="text-xs leading-relaxed text-muted-foreground">
              IFRC GO is a Red Cross Red Crescent platform to connect information on
              emergency needs with the right response.
            </p>
            <p className="mt-4 text-xs text-muted-foreground">© IFRC 2026 v7.24.0</p>
          </div>
          <div>
            <h3 className="mb-3 text-sm font-bold font-heading text-foreground">FIND OUT MORE</h3>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#" className="text-primary hover:underline">ifrc.org</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">rcrcsims.org</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">data.ifrc.org</a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-3 text-sm font-bold font-heading text-foreground">POLICIES</h3>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#" className="text-primary hover:underline">Cookie Policy</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">Terms and Conditions</a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-3 text-sm font-bold font-heading text-foreground">HELPFUL LINKS</h3>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#" className="text-primary hover:underline">Open Source Code</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">API Documentation</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">Other Resources</a>
              </li>
              <li>
                <a href="#" className="text-primary hover:underline">GO Wiki</a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-3 text-sm font-bold font-heading text-foreground">CONTACT US</h3>
            <a
              href="mailto:im@ifrc.org"
              className="inline-block rounded bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
            >
              im@ifrc.org ↗
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default IFRCFooter;
