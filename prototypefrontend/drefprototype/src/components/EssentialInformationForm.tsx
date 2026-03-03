import FormField from "./FormField";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ImageUploadButton from "./ImageUploadButton";
import { type EnrichedFormState } from "@/lib/api";

interface EssentialInformationFormProps {
  onBack: () => void;
  onContinue: () => void;
  formState?: EnrichedFormState;
  onFieldChange?: (fieldId: string, value: any) => void;
}

const getField = (formState: EnrichedFormState | undefined, fieldId: string): string => {
  const val = formState?.[fieldId]?.value;
  return val != null ? String(val) : "";
};

const EssentialInformationForm = ({ onBack, onContinue, formState, onFieldChange }: EssentialInformationFormProps) => {
  const field = (id: string) => getField(formState, id);
  const change = (id: string) => (value: string) => onFieldChange?.(id, value);

  return (
    <section>
      {/* Staging banner */}
      {/* <div className="mb-6 bg-ifrc-staging py-2 text-center text-sm font-bold tracking-wider text-primary-foreground">
        STAGING SITE
      </div> */}

      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        ESSENTIAL INFORMATION
      </h2>

      <div className="space-y-4">
        <FormField
          label="Name of National Society"
          description="Indicate your National Society by selecting it from the drop-down list."
          required
        >
          <Select value={field("operation_overview.national_society") || undefined} onValueChange={change("operation_overview.national_society")}>
            <SelectTrigger>
              <SelectValue placeholder="Select National Society" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Afghan Red Crescent Society">Afghan Red Crescent Society</SelectItem>
              <SelectItem value="Albanian Red Cross">Albanian Red Cross</SelectItem>
              <SelectItem value="Algerian Red Crescent">Algerian Red Crescent</SelectItem>
              <SelectItem value="Argentine Red Cross">Argentine Red Cross</SelectItem>
              <SelectItem value="Australian Red Cross">Australian Red Cross</SelectItem>
              <SelectItem value="Bangladesh Red Crescent Society">Bangladesh Red Crescent Society</SelectItem>
              <SelectItem value="British Red Cross">British Red Cross</SelectItem>
              <SelectItem value="Colombian Red Cross Society">Colombian Red Cross Society</SelectItem>
              <SelectItem value="Ethiopian Red Cross Society">Ethiopian Red Cross Society</SelectItem>
              <SelectItem value="French Red Cross">French Red Cross</SelectItem>
              <SelectItem value="German Red Cross">German Red Cross</SelectItem>
              <SelectItem value="Indian Red Cross Society">Indian Red Cross Society</SelectItem>
              <SelectItem value="Indonesian Red Cross Society">Indonesian Red Cross Society</SelectItem>
              <SelectItem value="Japanese Red Cross Society">Japanese Red Cross Society</SelectItem>
              <SelectItem value="Kenya Red Cross Society">Kenya Red Cross Society</SelectItem>
              <SelectItem value="Mexican Red Cross">Mexican Red Cross</SelectItem>
              <SelectItem value="Mozambique Red Cross Society">Mozambique Red Cross Society</SelectItem>
              <SelectItem value="Nepal Red Cross Society">Nepal Red Cross Society</SelectItem>
              <SelectItem value="Nigerian Red Cross Society">Nigerian Red Cross Society</SelectItem>
              <SelectItem value="Philippine Red Cross">Philippine Red Cross</SelectItem>
            </SelectContent>
          </Select>
        </FormField>

        <FormField
          label="Import data from existing field report"
          description='If a field report related to this event/operation already exists, you can use it to pre-fill matching fields in this request. To do so, select the relevant field report from the drop-down list and click "Copy".'
        >
          <div className="flex gap-2">
            <div className="flex-1">
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select field report" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fr-001">FR-2024-001: Mozambique Floods</SelectItem>
                  <SelectItem value="fr-002">FR-2024-002: Nepal Earthquake</SelectItem>
                  <SelectItem value="fr-003">FR-2024-003: Philippines Typhoon</SelectItem>
                  <SelectItem value="fr-004">FR-2024-004: Bangladesh Cyclone</SelectItem>
                  <SelectItem value="fr-005">FR-2024-005: Ethiopia Drought</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <button className="rounded-full border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Copy
            </button>
          </div>
        </FormField>

        <FormField label="DREF Type" required>
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Type of DREF</p>
            <Select value={field("operation_overview.dref_type") || undefined} onValueChange={change("operation_overview.dref_type")}>
              <SelectTrigger>
                <SelectValue placeholder="Select DREF type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Imminent Crisis">Imminent Crisis</SelectItem>
                <SelectItem value="Response">Response</SelectItem>
                <SelectItem value="Protracted Crisis">Protracted Crisis</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </FormField>

        <FormField label="Disaster Details">
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Type of Disaster</p>
                <Select value={field("operation_overview.disaster_type") || undefined} onValueChange={change("operation_overview.disaster_type")}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select disaster type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Flood">Flood</SelectItem>
                    <SelectItem value="Earthquake">Earthquake</SelectItem>
                    <SelectItem value="Cyclone">Cyclone / Hurricane / Typhoon</SelectItem>
                    <SelectItem value="Drought">Drought</SelectItem>
                    <SelectItem value="Epidemic">Epidemic</SelectItem>
                    <SelectItem value="Volcanic Eruption">Volcanic Eruption</SelectItem>
                    <SelectItem value="Fire">Wildfire</SelectItem>
                    <SelectItem value="Landslide">Landslide / Mudslide</SelectItem>
                    <SelectItem value="Tsunami">Tsunami</SelectItem>
                    <SelectItem value="Civil Unrest">Civil Unrest</SelectItem>
                    <SelectItem value="Population Movement">Population Movement / Conflict</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">
                  Type of Onset <span className="text-primary">*</span>
                </p>
                <Select value={field("operation_overview.disaster_onset") || undefined} onValueChange={change("operation_overview.disaster_onset")}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select onset type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Sudden">Sudden Onset</SelectItem>
                    <SelectItem value="Slow">Slow Onset</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">
                Disaster Category <span className="text-primary">*</span>
              </p>
              <Select value={field("operation_overview.disaster_category") || undefined} onValueChange={change("operation_overview.disaster_category")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select disaster category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Yellow">Yellow (Small-scale)</SelectItem>
                  <SelectItem value="Orange">Orange (Medium-scale)</SelectItem>
                  <SelectItem value="Red">Red (Large-scale)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </FormField>

        <FormField label="Affected Country and Affected Region(s)">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Add Country</p>
              <Select value={field("operation_overview.country") || undefined} onValueChange={change("operation_overview.country")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Afghanistan">Afghanistan</SelectItem>
                  <SelectItem value="Bangladesh">Bangladesh</SelectItem>
                  <SelectItem value="Brazil">Brazil</SelectItem>
                  <SelectItem value="Colombia">Colombia</SelectItem>
                  <SelectItem value="Ethiopia">Ethiopia</SelectItem>
                  <SelectItem value="Haiti">Haiti</SelectItem>
                  <SelectItem value="Indonesia">Indonesia</SelectItem>
                  <SelectItem value="Kenya">Kenya</SelectItem>
                  <SelectItem value="Madagascar">Madagascar</SelectItem>
                  <SelectItem value="Mozambique">Mozambique</SelectItem>
                  <SelectItem value="Nepal">Nepal</SelectItem>
                  <SelectItem value="Nigeria">Nigeria</SelectItem>
                  <SelectItem value="Pakistan">Pakistan</SelectItem>
                  <SelectItem value="Philippines">Philippines</SelectItem>
                  <SelectItem value="Somalia">Somalia</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Region/Province</p>
              <input
                type="text"
                value={field("operation_overview.region_province")}
                onChange={(e) => onFieldChange?.("operation_overview.region_province", e.target.value)}
                placeholder="Enter region or province"
                className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
        </FormField>

        <FormField label="DREF Title" required>
          <div className="flex gap-2">
            <div className="flex-1">
              <input
                type="text"
                value={field("operation_overview.dref_title")}
                onChange={(e) => onFieldChange?.("operation_overview.dref_title", e.target.value)}
                placeholder=""
                className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <button className="rounded-full border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Generate title
            </button>
          </div>
        </FormField>

        <FormField label="Emergency appeal planned">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="radio"
                name="emergency"
                className="accent-primary"
                checked={field("operation_overview.emergency_appeal_planned") === "true"}
                onChange={() => onFieldChange?.("operation_overview.emergency_appeal_planned", true)}
              />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="radio"
                name="emergency"
                className="accent-primary"
                checked={field("operation_overview.emergency_appeal_planned") === "false"}
                onChange={() => onFieldChange?.("operation_overview.emergency_appeal_planned", false)}
              />
              No
            </label>
          </div>
        </FormField>

        <FormField
          label="Upload map"
          description="Add a map highlighting the targeted areas for this operation, it will be used for the publicly published DREF application."
        >
          <ImageUploadButton label="Select an Image" />
        </FormField>

        <FormField
          label="Cover image"
          description="Upload a image for the cover page of the publicly published DREF application."
        >
          <ImageUploadButton label="Select an Image" />
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

export default EssentialInformationForm;
