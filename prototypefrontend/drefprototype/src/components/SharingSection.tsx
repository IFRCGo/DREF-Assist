import { Share2 } from "lucide-react";

const SharingSection = () => {
  return (
    <section className="mb-6">
      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">SHARING</h2>
      <div className="rounded border border-border bg-card p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold text-foreground">
              The DREF Application is shared with
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              The users will be able to view, edit and add other users.
            </p>
          </div>
          <button className="flex items-center gap-1 rounded-full border border-primary px-3 py-1.5 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
            <Share2 className="h-3 w-3" /> Add
          </button>
        </div>
        <div className="mt-6 flex flex-col items-center py-4">
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-muted">
            <span className="text-muted-foreground text-lg">👥</span>
          </div>
          <p className="text-sm text-muted-foreground">
            The DREF Application is not shared with anyone.
          </p>
        </div>
      </div>
    </section>
  );
};

export default SharingSection;
