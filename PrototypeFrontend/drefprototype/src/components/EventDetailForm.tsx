import FormField from "./FormField";
import { ChevronDown, Plus } from "lucide-react";

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
  return (
    <section>
      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        DESCRIPTION OF THE EVENT
      </h2>

      <div className="space-y-4">
        <FormField label="Date when the trigger was met">
          <DateInput />
        </FormField>

        <FormField label="Numeric Details">
          <div className="space-y-3">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Total affected population</p>
              <TextInput />
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">People in need (Optional)</p>
              <TextInput />
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
                <TextInput />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated female affected</p>
                <TextInput />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Girls (under 18)</p>
                <TextInput />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Boys (under 18)</p>
                <TextInput />
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
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder=""
          />
        </FormField>

        <FormField
          label="Source Information"
          description="Add the links and the name of the sources, the name will be shown in the export, as a hyperlink."
        >
          <button className="flex items-center gap-2 rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
            <Plus className="h-4 w-4" />
            Add New Source Information
          </button>
        </FormField>

        <FormField
          label="Upload photos"
          description="(e.g. impact of the events, NS in the field, assessments) Add maximum 4 photos"
        >
          <div>
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Select an Image
            </button>
            <p className="mt-2 text-xs text-muted-foreground">No file Selected</p>
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
      </div>
    </section>
  );
};

export default EventDetailForm;
