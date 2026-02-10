import FormField from "./FormField";
import { ChevronDown } from "lucide-react";

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

interface EssentialInformationFormProps {
  onBack: () => void;
  onContinue: () => void;
}

const EssentialInformationForm = ({ onBack, onContinue }: EssentialInformationFormProps) => {
  return (
    <section>
      {/* Staging banner */}
      <div className="mb-6 bg-ifrc-staging py-2 text-center text-sm font-bold tracking-wider text-primary-foreground">
        STAGING SITE
      </div>

      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        ESSENTIAL INFORMATION
      </h2>

      <div className="space-y-4">
        <FormField
          label="Name of National Society"
          description="Indicate your National Society by selecting it from the drop-down list."
          required
        >
          <SelectInput />
        </FormField>

        <FormField
          label="Import data from existing field report"
          description='If a field report related to this event/operation already exists, you can use it to pre-fill matching fields in this request. To do so, select the relevant field report from the drop-down list and click "Copy".'
        >
          <div className="flex gap-2">
            <div className="flex-1">
              <SelectInput placeholder="Select field report" />
            </div>
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Copy
            </button>
          </div>
        </FormField>

        <FormField label="DREF Type" required>
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Type of DREF</p>
            <SelectInput />
          </div>
        </FormField>

        <FormField label="Disaster Details">
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Type of Disaster</p>
                <SelectInput />
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">
                  Type of Onset <span className="text-primary">*</span>
                </p>
                <SelectInput />
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">
                Disaster Category <span className="text-primary">*</span>
              </p>
              <SelectInput />
            </div>
          </div>
        </FormField>

        <FormField label="Affected Country and Affected Region(s)">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Add Country</p>
              <SelectInput />
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Region/Province</p>
              <SelectInput />
            </div>
          </div>
        </FormField>

        <FormField label="DREF Title" required>
          <div className="flex gap-2">
            <div className="flex-1">
              <TextInput />
            </div>
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Generate title
            </button>
          </div>
        </FormField>

        <FormField label="Emergency appeal planned">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="emergency" className="accent-primary" />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="emergency" className="accent-primary" />
              No
            </label>
          </div>
        </FormField>

        <FormField
          label="Upload map"
          description="Add a map highlighting the targeted areas for this operation, it will be used for the publicly published DREF application."
        >
          <div>
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Select an Image
            </button>
            <p className="mt-2 text-xs text-muted-foreground">No file Selected</p>
          </div>
        </FormField>

        <FormField
          label="Cover image"
          description="Upload a image for the cover page of the publicly published DREF application."
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

export default EssentialInformationForm;
