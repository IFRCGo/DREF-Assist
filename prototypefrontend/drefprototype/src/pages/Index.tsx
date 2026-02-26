import { useState, useCallback } from "react";
import { Bot } from "lucide-react";
import IFRCHeader from "@/components/IFRCHeader";
import IFRCFooter from "@/components/IFRCFooter";
import StepIndicator from "@/components/StepIndicator";
import SharingSection from "@/components/SharingSection";
import EssentialInformationForm from "@/components/EssentialInformationForm";
import EventDetailForm from "@/components/EventDetailForm";
import ActionsNeedsForm from "@/components/ActionsNeedsForm";
import OperationForm from "@/components/OperationForm";
import TimeframesContactsForm from "@/components/TimeframesContactsForm";
import DREFAssistChat from "@/components/DREFAssistChat";
import { type EnrichedFormState, type FieldUpdate } from "@/lib/api";

const Index = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [formState, setFormState] = useState<EnrichedFormState>({});

  const goNext = () => setActiveStep((s) => Math.min(s + 1, 5));
  const goBack = () => setActiveStep((s) => Math.max(s - 1, 0));

  const handleFieldUpdates = useCallback((updates: FieldUpdate[]) => {
    setFormState((prev) => {
      const next = { ...prev };
      for (const update of updates) {
        next[update.field_id] = {
          value: update.value,
          source: update.source,
          timestamp: update.timestamp,
        };
      }
      return next;
    });
  }, []);

  const handleFieldChange = useCallback((fieldId: string, value: any) => {
    setFormState((prev) => ({
      ...prev,
      [fieldId]: {
        value,
        source: "user_input",
        timestamp: new Date().toISOString(),
      },
    }));
  }, []);

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
          <button
            onClick={() => setChatOpen((o) => !o)}
            className="flex items-center gap-1.5 rounded bg-accent px-4 py-1.5 text-sm font-semibold text-accent-foreground hover:opacity-90 transition-opacity"
          >
            <Bot className="h-4 w-4" />
            DREF Assist
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
          <EssentialInformationForm onBack={goBack} onContinue={goNext} formState={formState} onFieldChange={handleFieldChange} />
        )}
        {activeStep === 1 && (
          <EventDetailForm onBack={goBack} onContinue={goNext} formState={formState} onFieldChange={handleFieldChange} />
        )}
        {activeStep === 2 && (
          <ActionsNeedsForm onBack={goBack} onContinue={goNext} formState={formState} onFieldChange={handleFieldChange} />
        )}
        {activeStep === 3 && (
          <OperationForm onBack={goBack} onContinue={goNext} formState={formState} onFieldChange={handleFieldChange} />
        )}
        {activeStep === 4 && (
          <TimeframesContactsForm onBack={goBack} onContinue={goNext} formState={formState} onFieldChange={handleFieldChange} />
        )}
        {activeStep >= 5 && (
          <div className="py-12 text-center text-muted-foreground">
            <p className="text-sm">All steps completed.</p>
            <div className="mt-8 flex items-center justify-center gap-3">
              <button
                onClick={goBack}
                className="rounded border border-primary px-6 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
              >
                Back
              </button>
            </div>
          </div>
        )}
      </main>

      <IFRCFooter />

      <DREFAssistChat
        onClose={() => setChatOpen(false)}
        formState={formState}
        onFieldUpdates={handleFieldUpdates}
        isOpen={chatOpen}
      />
    </div>
  );
};

export default Index;
