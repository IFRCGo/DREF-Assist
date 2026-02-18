import FormField from "./FormField";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ImageUploadButton from "./ImageUploadButton";

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
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="Select National Society" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="afghan">Afghan Red Crescent Society</SelectItem>
              <SelectItem value="albanian">Albanian Red Cross</SelectItem>
              <SelectItem value="algerian">Algerian Red Crescent</SelectItem>
              <SelectItem value="argentinian">Argentine Red Cross</SelectItem>
              <SelectItem value="australian">Australian Red Cross</SelectItem>
              <SelectItem value="bangladesh">Bangladesh Red Crescent Society</SelectItem>
              <SelectItem value="british">British Red Cross</SelectItem>
              <SelectItem value="colombian">Colombian Red Cross Society</SelectItem>
              <SelectItem value="ethiopian">Ethiopian Red Cross Society</SelectItem>
              <SelectItem value="french">French Red Cross</SelectItem>
              <SelectItem value="german">German Red Cross</SelectItem>
              <SelectItem value="indian">Indian Red Cross Society</SelectItem>
              <SelectItem value="indonesian">Indonesian Red Cross Society</SelectItem>
              <SelectItem value="japanese">Japanese Red Cross Society</SelectItem>
              <SelectItem value="kenyan">Kenya Red Cross Society</SelectItem>
              <SelectItem value="mexican">Mexican Red Cross</SelectItem>
              <SelectItem value="mozambique">Mozambique Red Cross Society</SelectItem>
              <SelectItem value="nepal">Nepal Red Cross Society</SelectItem>
              <SelectItem value="nigerian">Nigerian Red Cross Society</SelectItem>
              <SelectItem value="philippine">Philippine Red Cross</SelectItem>
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
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Copy
            </button>
          </div>
        </FormField>

        <FormField label="DREF Type" required>
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Type of DREF</p>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Select DREF type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="imminent">Imminent Crisis</SelectItem>
                <SelectItem value="assessment">Assessment</SelectItem>
                <SelectItem value="response">Response</SelectItem>
                <SelectItem value="loan">Loan</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </FormField>

        <FormField label="Disaster Details">
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Type of Disaster</p>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select disaster type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="flood">Flood</SelectItem>
                    <SelectItem value="earthquake">Earthquake</SelectItem>
                    <SelectItem value="cyclone">Cyclone / Hurricane / Typhoon</SelectItem>
                    <SelectItem value="drought">Drought</SelectItem>
                    <SelectItem value="epidemic">Epidemic</SelectItem>
                    <SelectItem value="volcanic">Volcanic Eruption</SelectItem>
                    <SelectItem value="wildfire">Wildfire</SelectItem>
                    <SelectItem value="landslide">Landslide / Mudslide</SelectItem>
                    <SelectItem value="coldwave">Cold Wave</SelectItem>
                    <SelectItem value="heatwave">Heat Wave</SelectItem>
                    <SelectItem value="tsunami">Tsunami</SelectItem>
                    <SelectItem value="conflict">Population Movement / Conflict</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">
                  Type of Onset <span className="text-primary">*</span>
                </p>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select onset type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sudden">Sudden Onset</SelectItem>
                    <SelectItem value="slow">Slow Onset</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">
                Disaster Category <span className="text-primary">*</span>
              </p>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select disaster category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yellow">Yellow (Small-scale)</SelectItem>
                  <SelectItem value="orange">Orange (Medium-scale)</SelectItem>
                  <SelectItem value="red">Red (Large-scale)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </FormField>

        <FormField label="Affected Country and Affected Region(s)">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Add Country</p>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="af">Afghanistan</SelectItem>
                  <SelectItem value="bd">Bangladesh</SelectItem>
                  <SelectItem value="br">Brazil</SelectItem>
                  <SelectItem value="co">Colombia</SelectItem>
                  <SelectItem value="et">Ethiopia</SelectItem>
                  <SelectItem value="ht">Haiti</SelectItem>
                  <SelectItem value="id">Indonesia</SelectItem>
                  <SelectItem value="ke">Kenya</SelectItem>
                  <SelectItem value="mg">Madagascar</SelectItem>
                  <SelectItem value="mz">Mozambique</SelectItem>
                  <SelectItem value="np">Nepal</SelectItem>
                  <SelectItem value="ng">Nigeria</SelectItem>
                  <SelectItem value="pk">Pakistan</SelectItem>
                  <SelectItem value="ph">Philippines</SelectItem>
                  <SelectItem value="so">Somalia</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Region/Province</p>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="africa">Africa</SelectItem>
                  <SelectItem value="americas">Americas</SelectItem>
                  <SelectItem value="asia-pacific">Asia Pacific</SelectItem>
                  <SelectItem value="europe">Europe</SelectItem>
                  <SelectItem value="mena">Middle East & North Africa</SelectItem>
                </SelectContent>
              </Select>
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
