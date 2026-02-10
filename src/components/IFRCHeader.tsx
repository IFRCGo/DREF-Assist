import { Search, ChevronDown } from "lucide-react";
const navItems = [{
  label: "Home",
  hasDropdown: false
}, {
  label: "Countries",
  hasDropdown: true
}, {
  label: "Prepare",
  hasDropdown: true
}, {
  label: "Respond",
  hasDropdown: true
}, {
  label: "Learn",
  hasDropdown: true
}];
const IFRCHeader = () => {
  return <header>
      {/* Top bar */}
      <div className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            {/* IFRC Logo placeholder */}
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
                <span className="text-sm font-bold text-primary-foreground">GO</span>
              </div>
              <span className="text-lg font-bold text-primary font-heading">+IFRC+<span className="text-primary">+</span>CIFRC
              </span>
              <span className="ml-1 rounded bg-ifrc-staging px-2 text-xs font-semibold text-primary-foreground py-[3px]">
                staging
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button className="flex items-center gap-1 text-foreground">
              English <ChevronDown className="h-3 w-3" />
            </button>
            <button className="flex items-center gap-1 text-foreground">
              Team 24 <ChevronDown className="h-3 w-3" />
            </button>
            <button className="rounded border border-primary px-4 py-1.5 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Create a Report →
            </button>
          </div>
        </div>
      </div>

      {/* Navigation bar */}
      <div className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">
          <nav className="flex items-center gap-6">
            {navItems.map(item => <button key={item.label} className="flex items-center gap-1 text-sm text-foreground hover:text-primary transition-colors">
                {item.label}
                {item.hasDropdown && <ChevronDown className="h-3 w-3" />}
              </button>)}
          </nav>
          <div className="flex items-center gap-2 rounded border border-border px-3 py-1.5">
            <Search className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Search</span>
          </div>
        </div>
      </div>

      {/* Red top border line */}
      <div className="h-0.5 bg-primary" />
    </header>;
};
export default IFRCHeader;