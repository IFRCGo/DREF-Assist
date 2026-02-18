import FormField from "@/components/FormField";
import { Input } from "@/components/ui/input";

interface Props {
  onBack: () => void;
  onContinue: () => void;
}

const ContactBlock = ({ role, note }: { role: string; note?: string }) => (
  <FormField label={role} description={note}>
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <Input placeholder="Name" />
      <Input placeholder="Title" />
      <Input placeholder="Email" type="email" />
      <Input placeholder="Phone Number" type="tel" />
    </div>
  </FormField>
);

const TimeframesContactsForm = ({ onBack, onContinue }: Props) => {
  return (
    <div className="space-y-6 py-4">
      {/* ── OPERATIONAL TIMEFRAMES ── */}
      <h2 className="text-lg font-bold text-foreground">Operational Timeframes</h2>

      <FormField label="Date of National Society Application">
        <Input type="date" />
      </FormField>

      <FormField label="Date of Submission to GVA" description="Added by Regional Office">
        <Input type="date" />
      </FormField>

      <FormField label="Date of Approval">
        <Input type="date" />
      </FormField>

      <FormField label="Operation timeframe (months)">
        <Input type="number" placeholder="Input number of months" min={1} />
      </FormField>

      <FormField
        label="End date of Operation"
        description="Automatically calculated using the Date of Approval + Operation timeframe"
      >
        <Input type="date" />
      </FormField>

      <FormField label="Date of Publishing" description="Added by Regional Office">
        <Input type="date" />
      </FormField>

      {/* ── STAGING SITE ── */}
      <h2 className="text-lg font-bold text-foreground">Staging Site</h2>
      {/* placeholder – no fields visible in the PDF for this section */}

      {/* ── TRACKING DATA AND CONTACTS ── */}
      <h2 className="text-lg font-bold text-foreground">Tracking Data and Contacts</h2>

      <FormField label="Appeal Code" description="Added by the regional PMER">
        <Input placeholder="Appeal Code" />
      </FormField>

      <FormField label="GLIDE number">
        <Input placeholder="GLIDE number" />
      </FormField>

      <ContactBlock role="IFRC Appeal Manager" note="Added by the regional office" />
      <ContactBlock role="IFRC Project Manager" note="Added by the regional office" />
      <ContactBlock role="National Society Contact" />
      <ContactBlock role="IFRC Focal Point for the Emergency" />
      <ContactBlock role="DREF Regional Focal Point" />
      <ContactBlock role="Media Contact" />
      <ContactBlock role="National Societies' Integrity Focal Point" />

      <FormField label="National Society Hotline">
        <Input placeholder="Phone Number" type="tel" />
      </FormField>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
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
          Save
        </button>
      </div>
    </div>
  );
};

export default TimeframesContactsForm;
