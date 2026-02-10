import FormField from "./FormField";
import { Plus } from "lucide-react";

const TextArea = ({ placeholder, rows = 4 }: { placeholder?: string; rows?: number }) => (
  <textarea
    rows={rows}
    placeholder={placeholder}
    className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
  />
);

interface ActionsNeedsFormProps {
  onBack: () => void;
  onContinue: () => void;
}

const ActionsNeedsForm = ({ onBack, onContinue }: ActionsNeedsFormProps) => {
  return (
    <section>
      <h2 className="mb-4 text-lg font-bold font-heading text-foreground">
        CURRENT NATIONAL SOCIETY ACTIONS
      </h2>

      <div className="space-y-4">
        <FormField
          label="Current National Society Actions"
          description="Please indicate a description of the ongoing response with if possible: Branches involved, number of volunteers/staff involved in actions, assets deployed/distributed, number of people reached. Impact/added value of the NS in the response already ongoing."
        >
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <p className="text-sm text-foreground">Has the National Society started any actions?</p>
              <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                <input type="radio" name="ns-actions" className="accent-primary" />
                Yes
              </label>
              <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                <input type="radio" name="ns-actions" className="accent-primary" />
                No
              </label>
            </div>
            <p className="text-sm text-muted-foreground">Select the actions that apply.</p>
            <button className="flex items-center gap-2 rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              <Plus className="h-4 w-4" />
              Add
            </button>
          </div>
        </FormField>
      </div>

      {/* IFRC Network Actions */}
      <h2 className="mb-4 mt-8 text-lg font-bold font-heading text-foreground">
        IFRC NETWORK ACTIONS RELATED TO THE CURRENT EVENT
      </h2>

      <div className="space-y-4">
        <FormField
          label="IFRC"
          description="Presence or not of IFRC in country (if not, indicate the cluster covering), support provided for this response, domestic coordination, technical, strategic, surge. Explain what support provided in terms of Secretariat services: PMER, Finance, Admin, HR, Security, logistics, NSD."
        >
          <TextArea placeholder="Description" />
        </FormField>

        <FormField
          label="Participating National Societies"
          description="Briefly set out which PNS are present and give details of PNS contributions/roles on the ground and remotely for this specific operation."
        >
          <TextArea placeholder="" />
        </FormField>
      </div>

      {/* ICRC Actions */}
      <h2 className="mb-4 mt-8 text-lg font-bold font-heading text-foreground">
        ICRC ACTIONS RELATED TO THE CURRENT EVENT
      </h2>

      <div className="space-y-4">
        <FormField
          label="ICRC"
          description="Presence or not of ICRC in country, and support directly provided for this emergency response. Other programs and support provided outside of the scope of this emergency should not be indicated here."
        >
          <TextArea placeholder="Description" />
        </FormField>
      </div>

      {/* Other Actors */}
      <h2 className="mb-4 mt-8 text-lg font-bold font-heading text-foreground">
        OTHER ACTORS ACTIONS RELATED TO THE CURRENT EVENT
      </h2>

      <div className="space-y-4">
        <FormField label="Government request">
          <div className="flex items-center gap-4">
            <p className="text-sm text-foreground">Government has requested international assistance</p>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="gov-request" className="accent-primary" />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="gov-request" className="accent-primary" />
              No
            </label>
          </div>
        </FormField>

        <FormField label="National authorities" description="Brief description of actions taken by the national authorities.">
          <TextArea placeholder="" />
        </FormField>

        <FormField label="UN or other actors" description="Brief description of actions taken by the UN or other actors.">
          <TextArea placeholder="" />
        </FormField>

        <FormField label="Coordination mechanisms">
          <div className="flex items-center gap-4">
            <p className="text-sm text-foreground">Are there major coordination mechanisms in place?</p>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="coordination" className="accent-primary" />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="coordination" className="accent-primary" />
              No
            </label>
          </div>
        </FormField>
      </div>

      {/* Needs Identified */}
      <h2 className="mb-4 mt-8 text-lg font-bold font-heading text-foreground">
        NEEDS (GAPS) IDENTIFIED
      </h2>

      <div className="space-y-4">
        <FormField label="Upload assessment report" description="Assessment report file type: pdf, docx, pptx, xlsx.">
          <div>
            <button className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              Select an Image
            </button>
            <p className="mt-2 text-xs text-muted-foreground">No file Selected</p>
          </div>
        </FormField>

        <FormField label="Needs identified">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Select the needs that apply.</p>
            <button className="flex items-center gap-2 rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
              <Plus className="h-4 w-4" />
              Add
            </button>
          </div>
        </FormField>

        <FormField
          label="Any identified gaps/limitations in the assessment"
          description="Consider the following:"
        >
          <div className="space-y-3">
            <div className="rounded border border-border bg-muted/30 p-3 text-xs text-muted-foreground leading-relaxed">
              <ul className="list-disc pl-4 space-y-1">
                <li><strong>Unmet needs:</strong> are there specific sectors (e.g., shelter, WASH, health) where needs remain unmet or only partially addressed?</li>
                <li><strong>Resource shortages:</strong> highlight any shortages in available resources (e.g., funding, personnel, supplies) that limit the ability to meet the identified needs.</li>
                <li><strong>Operational challenges:</strong> mention any operational constraints that are preventing a full response to the needs (e.g., logistical issues, insufficient capacity).</li>
                <li><strong>Coordination issues:</strong> note any challenges in coordinating with other actors or agencies that have resulted in gaps in service delivery or response coverage.</li>
                <li><strong>Vulnerable groups:</strong> identify any specific vulnerable groups whose needs may not have been fully captured or addressed during the assessment (e.g., displaced persons, elderly, people with disabilities).</li>
              </ul>
            </div>
            <TextArea placeholder="Description" rows={5} />
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

export default ActionsNeedsForm;
