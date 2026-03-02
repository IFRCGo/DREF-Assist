import FormField from "@/components/FormField";
import { Input } from "@/components/ui/input";
import { type EnrichedFormState } from "@/lib/api";

interface Props {
  onBack: () => void;
  onContinue: () => void;
  formState?: EnrichedFormState;
  onFieldChange?: (fieldId: string, value: any) => void;
}

const getField = (formState: EnrichedFormState | undefined, fieldId: string): string => {
  const val = formState?.[fieldId]?.value;
  return val != null ? String(val) : "";
};

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

const TimeframesContactsForm = ({ onBack, onContinue, formState, onFieldChange }: Props) => {
  const field = (id: string) => getField(formState, id);
  const change = (id: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onFieldChange?.(id, e.target.value);

  return (
    <div className="space-y-6 py-4">
      {/* ── OPERATIONAL TIMEFRAMES ── */}
      <h2 className="text-lg font-bold text-foreground">Operational Timeframes</h2>

      <FormField label="Date of National Society Application">
        <Input type="date" value={field("timeframes_contacts.ns_application_date")} onChange={change("timeframes_contacts.ns_application_date")} />
      </FormField>

      <FormField label="Date of Submission to GVA" description="Added by Regional Office">
        <Input type="date" />
      </FormField>

      <FormField label="Date of Approval">
        <Input type="date" />
      </FormField>

      <FormField label="Operation timeframe (months)">
        <Input type="number" placeholder="Input number of months" min={1} value={field("timeframes_contacts.operation_timeframe_months")} onChange={change("timeframes_contacts.operation_timeframe_months")} />
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
        <Input placeholder="Appeal Code" value={field("timeframes_contacts.appeal_code")} onChange={change("timeframes_contacts.appeal_code")} />
      </FormField>

      <FormField label="GLIDE number">
        <Input placeholder="GLIDE number" value={field("timeframes_contacts.glide_number")} onChange={change("timeframes_contacts.glide_number")} />
      </FormField>

      <ContactBlock role="IFRC Appeal Manager" note="Added by the regional office" />
      <ContactBlock role="IFRC Project Manager" note="Added by the regional office" />

      {/* National Society Contact — wired to state */}
      <FormField label="National Society Contact">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={field("timeframes_contacts.ns_contact_name")} onChange={change("timeframes_contacts.ns_contact_name")} />
          <Input placeholder="Title" value={field("timeframes_contacts.ns_contact_title")} onChange={change("timeframes_contacts.ns_contact_title")} />
          <Input placeholder="Email" type="email" value={field("timeframes_contacts.ns_contact_email")} onChange={change("timeframes_contacts.ns_contact_email")} />
          <Input placeholder="Phone Number" type="tel" value={field("timeframes_contacts.ns_contact_phone")} onChange={change("timeframes_contacts.ns_contact_phone")} />
        </div>
      </FormField>

      <ContactBlock role="IFRC Focal Point for the Emergency" />
      <ContactBlock role="DREF Regional Focal Point" />
      <ContactBlock role="Media Contact" />
      <ContactBlock role="National Societies' Integrity Focal Point" />

      <FormField label="National Society Hotline">
        <Input placeholder="Phone Number" type="tel" />
      </FormField>

      {/* Navigation */}
      <div className="flex items-center justify-center gap-2 pt-4">
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
          Save
        </button>
      </div>
    </div>
  );
};

export default TimeframesContactsForm;
