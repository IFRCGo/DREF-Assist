import FormField from "./FormField";
import { Plus } from "lucide-react";
import ImageUploadButton from "./ImageUploadButton";
import { type EnrichedFormState } from "@/lib/api";

interface EventDetailFormProps {
  onBack: () => void;
  onContinue: () => void;
  formState?: EnrichedFormState;
  onFieldChange?: (fieldId: string, value: any) => void;
}

const getField = (formState: EnrichedFormState | undefined, fieldId: string): string => {
  const val = formState?.[fieldId]?.value;
  return val != null ? String(val) : "";
};

const EventDetailForm = ({ onBack, onContinue, formState, onFieldChange }: EventDetailFormProps) => {
  const field = (id: string) => getField(formState, id);
  const change = (id: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    onFieldChange?.(id, e.target.value);

  return (
    <section>
      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        DESCRIPTION OF THE EVENT
      </h2>

      <div className="space-y-4">
        <FormField label="Date when the trigger was met">
          <input
            type="date"
            value={field("event_detail.date_trigger_met")}
            onChange={change("event_detail.date_trigger_met")}
            placeholder="dd/mm/yyyy"
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </FormField>

        <FormField label="Numeric Details">
          <div className="space-y-3">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Total affected population</p>
              <input
                type="number"
                value={field("event_detail.total_affected_population")}
                onChange={change("event_detail.total_affected_population")}
                className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">People in need (Optional)</p>
              <input
                type="number"
                value={field("event_detail.people_in_need")}
                onChange={change("event_detail.people_in_need")}
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
                  type="number"
                  value={field("event_detail.estimated_male_affected")}
                  onChange={change("event_detail.estimated_male_affected")}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated female affected</p>
                <input
                  type="number"
                  value={field("event_detail.estimated_female_affected")}
                  onChange={change("event_detail.estimated_female_affected")}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Girls (under 18)</p>
                <input
                  type="number"
                  value={field("event_detail.estimated_girls_under_18")}
                  onChange={change("event_detail.estimated_girls_under_18")}
                  className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Estimated Boys (under 18)</p>
                <input
                  type="number"
                  value={field("event_detail.estimated_boys_under_18")}
                  onChange={change("event_detail.estimated_boys_under_18")}
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
            value={field("event_detail.what_happened")}
            onChange={change("event_detail.what_happened")}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder=""
          />
        </FormField>

        <FormField
          label="Source Information"
          description="Add the links and the name of the sources, the name will be shown in the export, as a hyperlink."
        >
          <button className="flex items-center gap-2 rounded-full border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
            <Plus className="h-4 w-4" />
            Add New Source Information
          </button>
        </FormField>

        <FormField
          label="Upload photos"
          description="(e.g. impact of the events, NS in the field, assessments) Add maximum 4 photos"
        >
          <ImageUploadButton label="Select an Image" maxFiles={4} />
        </FormField>
      </div>

      {/* Navigation buttons */}
      <div className="mt-8 flex items-center justify-center gap-3">
        <button
          onClick={onBack}
          className="rounded-full border border-primary px-5 py-1 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
        >
          Back
        </button>
        <button
          onClick={onContinue}
          className="rounded-full border border-primary px-5 py-1 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
        >
          Continue
        </button>
      </div>
    </section>
  );
};

export default EventDetailForm;
