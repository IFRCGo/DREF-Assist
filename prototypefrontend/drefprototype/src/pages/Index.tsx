import { useState, useCallback } from "react";
import { Bot, CheckCircle2, ClipboardCheck } from "lucide-react";
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
import EvaluationPanel from "@/components/EvaluationPanel";
import FinalEvaluationDialog from "@/components/FinalEvaluationDialog";
import ReviewSubmitPage from "@/components/ReviewSubmitPage";
import {
  type EnrichedFormState,
  type FieldUpdate,
  type EvaluationResult,
  evaluateDref,
} from "@/lib/api";

const Index = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [formState, setFormState] = useState<EnrichedFormState>({});

  // Evaluation state
  const [evaluationResult, setEvaluationResult] =
    useState<EvaluationResult | null>(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationOpen, setEvaluationOpen] = useState(false);

  // Final evaluation dialog state
  const [finalEvalOpen, setFinalEvalOpen] = useState(false);
  const [finalEvalLoading, setFinalEvalLoading] = useState(false);

  // Pending message for chat (set by "Improve with AI" buttons)
  const [pendingChatMessage, setPendingChatMessage] = useState<string | null>(
    null,
  );

  const goNext = () => setActiveStep((s) => Math.min(s + 1, 6));
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

  const handleEvaluate = useCallback(async () => {
    setEvaluationLoading(true);
    setEvaluationOpen(true);
    try {
      const result = await evaluateDref(formState);
      setEvaluationResult(result);
    } catch (err) {
      console.error("Evaluation failed:", err);
    } finally {
      setEvaluationLoading(false);
    }
  }, [formState]);

  const handleSave = useCallback(async () => {
    setFinalEvalLoading(true);
    setFinalEvalOpen(true);
    try {
      const result = await evaluateDref(formState);
      setEvaluationResult(result);
    } catch (err) {
      console.error("Evaluation failed:", err);
    } finally {
      setFinalEvalLoading(false);
    }
  }, [formState]);

  const handleViewDetails = useCallback(() => {
    setFinalEvalOpen(false);
    setEvaluationOpen(true);
  }, []);

  const handleFinalEvalDone = useCallback(() => {
    setFinalEvalOpen(false);
    setActiveStep(5);
  }, []);

  const handleSubmit = useCallback(() => {
    setActiveStep(6);
  }, []);

  const handleRequestImprovement = useCallback((prompt: string) => {
    setPendingChatMessage(prompt);
    setChatOpen(true);
    setEvaluationOpen(false);
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
            onClick={handleEvaluate}
            disabled={evaluationLoading}
            className="flex items-center gap-1.5 rounded border border-primary px-4 py-1.5 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors disabled:opacity-50"
          >
            <ClipboardCheck className="h-4 w-4" />
            Evaluate
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
          <EssentialInformationForm
            onBack={goBack}
            onContinue={goNext}
            formState={formState}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeStep === 1 && (
          <EventDetailForm
            onBack={goBack}
            onContinue={goNext}
            formState={formState}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeStep === 2 && (
          <ActionsNeedsForm
            onBack={goBack}
            onContinue={goNext}
            formState={formState}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeStep === 3 && (
          <OperationForm
            onBack={goBack}
            onContinue={goNext}
            formState={formState}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeStep === 4 && (
          <TimeframesContactsForm
            onBack={goBack}
            onContinue={handleSave}
            formState={formState}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeStep === 5 && (
          <ReviewSubmitPage
            onBack={goBack}
            onSubmit={handleSubmit}
            formState={formState}
          />
        )}
        {activeStep >= 6 && (
          <div className="py-16 text-center">
            <CheckCircle2 className="mx-auto h-16 w-16 text-green-600" />
            <h2 className="mt-4 text-2xl font-bold text-foreground">
              Thank You!
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Your DREF application has been submitted successfully.
            </p>
            <div className="mt-8">
              <button
                onClick={() => setActiveStep(0)}
                className="rounded bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                Return to DREF Application
              </button>
            </div>
          </div>
        )}
      </main>

      <IFRCFooter />

      {/* Final evaluation dialog */}
      <FinalEvaluationDialog
        open={finalEvalOpen}
        onOpenChange={setFinalEvalOpen}
        result={evaluationResult}
        loading={finalEvalLoading}
        onViewDetails={handleViewDetails}
        onDone={handleFinalEvalDone}
      />

      {/* Evaluation panel */}
      <EvaluationPanel
        open={evaluationOpen}
        onOpenChange={setEvaluationOpen}
        result={evaluationResult}
        loading={evaluationLoading}
        onRequestImprovement={handleRequestImprovement}
      />

      {/* Chat */}
      <DREFAssistChat
        onClose={() => setChatOpen(false)}
        formState={formState}
        onFieldUpdates={handleFieldUpdates}
        isOpen={chatOpen}
        pendingMessage={pendingChatMessage}
        onPendingMessageConsumed={() => setPendingChatMessage(null)}
      />
    </div>
  );
};

export default Index;
