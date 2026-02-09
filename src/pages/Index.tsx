import IFRCHeader from "@/components/IFRCHeader";
import IFRCFooter from "@/components/IFRCFooter";
import StepIndicator from "@/components/StepIndicator";
import SharingSection from "@/components/SharingSection";
import EssentialInformationForm from "@/components/EssentialInformationForm";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <IFRCHeader />

      {/* Page content */}
      <main className="mx-auto max-w-4xl px-4 py-6">
        {/* Top actions */}
        <div className="mb-4 flex justify-end gap-2">
          <button className="rounded border border-primary px-4 py-1.5 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
            Import
          </button>
          <button className="rounded bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity">
            Save
          </button>
        </div>

        {/* Title */}
        <div className="mb-2 text-center">
          <h1 className="text-3xl font-bold font-heading text-foreground">
            DREF Application
          </h1>
          <a
            href="#"
            className="mt-2 inline-block text-sm text-primary underline hover:opacity-80"
          >
            Provide feedback on IFRC DREF ↗
          </a>
        </div>

        {/* Step indicator */}
        <StepIndicator />

        {/* Sharing section */}
        <SharingSection />

        {/* Essential information form */}
        <EssentialInformationForm />
      </main>

      <IFRCFooter />
    </div>
  );
};

export default Index;
