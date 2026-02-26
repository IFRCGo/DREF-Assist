import FormField from "./FormField";
import { ChevronDown, Plus } from "lucide-react";
import ImageUploadButton from "./ImageUploadButton";
import { useState } from "react";
import EvaluationModal from "./EvaluationModal";

const SelectInput = ({ placeholder }: { placeholder?: string }) => (
  <div className="flex items-center rounded border border-input bg-card px-3 py-2">
    <span className="flex-1 text-sm text-muted-foreground">{placeholder}</span>
    <ChevronDown className="h-4 w-4 text-muted-foreground" />
  </div>
);

const TextInput = ({ placeholder }: { placeholder?: string }) => (
  <input
    type="text"
    placeholder={placeholder}
    className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
  />
);

const DateInput = ({ placeholder }: { placeholder?: string }) => (
  <input
    type="text"
    placeholder={placeholder || "dd/mm/yyyy"}
    className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
  />
);

interface EventDetailFormProps {
  onBack: () => void;
  onContinue: () => void;
}

const EventDetailForm = ({ onBack, onContinue }: EventDetailFormProps) => {
  // Form state
  const [triggerDate, setTriggerDate] = useState("");
  const [totalAffected, setTotalAffected] = useState("");
  const [peopleInNeed, setPeopleInNeed] = useState("");
  const [maleAffected, setMaleAffected] = useState("");
  const [femaleAffected, setFemaleAffected] = useState("");
  const [girlsUnder18, setGirlsUnder18] = useState("");
  const [boysUnder18, setBoysUnder18] = useState("");
  const [eventDescription, setEventDescription] = useState("");
  const [sourceInfo, setSourceInfo] = useState("");
  const [photosUploaded, setPhotosUploaded] = useState(false);

  // Evaluation state
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    setShowModal(true);
    try {
      const formData = {
        trigger_date: triggerDate,
        total_affected_population: totalAffected,
        people_in_need: peopleInNeed,
        male_affected: maleAffected,
        female_affected: femaleAffected,
        girls_under_18: girlsUnder18,
        boys_under_18: boysUnder18,
        event_description: eventDescription,
        source_information: sourceInfo,
        photos_upload: photosUploaded,
      };
      const response = await fetch(
        "http://localhost:8000/api/v2/dref-evaluation/ai-evaluate/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ form_data: formData, section: "event_detail" }),
        }
      );
      const result = await response.json();
      setEvaluationResult(result);
    } catch (error) {
      setEvaluationResult({ error: `Failed to evaluate: ${(error as Error).message}` });
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <section>
      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        DESCRIPTION OF THE EVENT
      </h2>

      <div className="space-y-4">
        <FormField label="Date when the trigger was met">
          <input
            type="text"
            placeholder="dd/mm/yyyy"
            value={triggerDate}
            onChange={(e) => setTriggerDate(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </FormField>

        <FormField label="Numeric Details">
          <div className="space-y-3">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Total affected population</p>
              <input
                type="text"
                placeholder="Enter number"
                value={totalAffected}
                onChange={(e) => setTotalAffected(e.target.value)}
                className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">People in need (Optional)</p>
              <input
                type="text"
                placeholder="Enter number or leave blank"
                value={peopleInNeed}
                onChange={(e) => setPeopleInNeed(e.target.value)}
                className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="rounded border border-border bg-muted/30 p-3 text-xs text-muted-foreground leading-relaxed space-y-2">
              <p>
                <strong>People Affected</strong> include all those whose lives and livelihoods have been impacted as a direct result of the shock or stress.
              </p>
              <p>
                <strong>People in Need (PIN)</strong> are those members whose physical security, basic rights, dignity, living conditions or livelihoods are threatened or have been disrupted, and whose current level of access to basic services, goods and social protection is inadequate to re-establish normal living conditions without additional assistance.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated male affected</p>
                <input
                  type="text"
                  placeholder="Enter number"
                  value={maleAffected}
                  onChange={(e) => setMaleAffected(e.target.value)}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated female affected</p>
                <input
                  type="text"
                  placeholder="Enter number"
                  value={femaleAffected}
                  onChange={(e) => setFemaleAffected(e.target.value)}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Girls (under 18)</p>
                <input
                  type="text"
                  placeholder="Enter number"
                  value={girlsUnder18}
                  onChange={(e) => setGirlsUnder18(e.target.value)}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Boys (under 18)</p>
                <input
                  type="text"
                  placeholder="Enter number"
                  value={boysUnder18}
                  onChange={(e) => setBoysUnder18(e.target.value)}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
          </div>
        </FormField>

        <FormField
          label="What happened, where and when?"
          description="Clearly Describe: 1) What happened: Briefly explain the nature of the emergency. 2) Where: Specify the geographic location(s) affected. 3) When: Indicate the date and time when the event occurred or began."
        >
          <textarea
            rows={5}
            value={eventDescription}
            onChange={(e) => setEventDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder="Describe what happened, where it occurred, and when..."
          />
        </FormField>

        <FormField
          label="Source Information"
          description="Add the links and the name of the sources, the name will be shown in the export, as a hyperlink."
        >
          <input
            type="text"
            placeholder="Enter source information"
            value={sourceInfo}
            onChange={(e) => setSourceInfo(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </FormField>

        <FormField
          label="Upload photos"
          description="(e.g. impact of the events, NS in the field, assessments) Add maximum 4 photos"
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPhotosUploaded(!photosUploaded)}
              className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              {photosUploaded ? "✓ Photos Uploaded" : "Select Images"}
            </button>
            {photosUploaded && <span className="text-xs text-green-600">Photos uploaded</span>}
          </div>
        </FormField>
      </div>

      {/* Navigation buttons */}
      <div className="mt-8 flex items-center justify-center gap-3">
        <button
          onClick={onBack}
          className="rounded border border-primary px-6 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
        >
          Back
        </button>
        <button
          onClick={onContinue}
          className="rounded bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
        >
          Continue
        </button>
        <button
          onClick={handleEvaluate}
          disabled={isEvaluating}
          className="rounded bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isEvaluating ? "Evaluating..." : "Evaluate"}
        </button>
      </div>
      <EvaluationModal
        isOpen={showModal}
        result={evaluationResult}
        isLoading={isEvaluating}
        onClose={() => {
          setShowModal(false);
          setEvaluationResult(null);
        }}
        formData={{
          trigger_date: triggerDate,
          total_affected_population: totalAffected,
          people_in_need: peopleInNeed,
          male_affected: maleAffected,
          female_affected: femaleAffected,
          girls_under_18: girlsUnder18,
          boys_under_18: boysUnder18,
          event_description: eventDescription,
          source_information: sourceInfo,
          photos_upload: photosUploaded,
        }}
      />
    </section>
  );
};

export default EventDetailForm;
