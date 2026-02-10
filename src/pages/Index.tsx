import { useState } from "react";
import IFRCHeader from "@/components/IFRCHeader";
import IFRCFooter from "@/components/IFRCFooter";
import StepIndicator from "@/components/StepIndicator";
import SharingSection from "@/components/SharingSection";
import EssentialInformationForm from "@/components/EssentialInformationForm";
import EventDetailForm from "@/components/EventDetailForm";
import ActionsNeedsForm from "@/components/ActionsNeedsForm";

const Index = () => {
  const [activeStep, setActiveStep] = useState(0);

  const goNext = () => setActiveStep((s) => Math.min(s + 1, 4));
  const goBack = () => setActiveStep((s) => Math.max(s - 1, 0));

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
        <StepIndicator activeStep={activeStep} />

        {/* Sharing section - only on first step */}
        {activeStep === 0 && <SharingSection />}

        {/* Step content */}
        {activeStep === 0 && (
          <EssentialInformationForm onBack={goBack} onContinue={goNext} />
        )}
        {activeStep === 1 && (
          <EventDetailForm onBack={goBack} onContinue={goNext} />
        )}
        {activeStep === 2 && (
          <ActionsNeedsForm onBack={goBack} onContinue={goNext} />
        )}
        {activeStep >= 3 && (
          <div className="py-12 text-center text-muted-foreground">
            <p className="text-sm">This step is under construction.</p>
            <div className="mt-8 flex items-center justify-center gap-3">
              <button
                onClick={goBack}
                className="rounded border border-primary px-6 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
              >
                Back
              </button>
              <button
                onClick={goNext}
                className="rounded bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                Continue
              </button>
            </div>
          </div>
        )}
      </main>

      <IFRCFooter />
    </div>
  );
};

export default Index;
