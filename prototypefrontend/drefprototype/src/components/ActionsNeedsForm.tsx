import FormField from "./FormField";
import { Plus, ChevronDown } from "lucide-react";
import ImageUploadButton from "./ImageUploadButton";
import { useState } from "react";
import { type EnrichedFormState } from "@/lib/api";

const actionOptions = [
    "Shelter, Housing And Settlements",
    "Multi Purpose Cash",
    "Health",
    "Water, Sanitation and Hygiene",
    "Protection, Gender and Inclusion",
    "Education",
    "Migration And Displacement",
    "Risk Reduction, Climate Adaptation And Recovery",
    "Community Engagement and Accountability",
    "Environment Sustainability",
    "Coordination",
    "National Society Readiness",
    "Assessment",
    "Resource Mobilization",
    "Activation Of Contingency Plans",
    "National Society EOC",
    "Other"
];

interface ActionsNeedsFormProps {
    onBack: () => void;
    onContinue: () => void;
    formState?: EnrichedFormState;
    onFieldChange?: (fieldId: string, value: any) => void;
}

const getField = (formState: EnrichedFormState | undefined, fieldId: string): string => {
    const val = formState?.[fieldId]?.value;
    return val != null ? String(val) : "";
};

const ActionsNeedsForm = ({ onBack, onContinue, formState, onFieldChange }: ActionsNeedsFormProps) => {
    const [selectedActions, setSelectedActions] = useState<string[]>([]);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    const field = (id: string) => getField(formState, id);
    const change = (id: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        onFieldChange?.(id, e.target.value);

    const handleActionSelect = (action: string) => {
        if (!selectedActions.includes(action)) {
            setSelectedActions([...selectedActions, action]);
        }
        setIsDropdownOpen(false);
    };

    const removeAction = (action: string) => {
        setSelectedActions(selectedActions.filter(a => a !== action));
    };

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
                                <input type="radio" name="ns-actions" className="accent-primary" checked={field("actions_needs.ns_actions_started") === "true"} onChange={() => onFieldChange?.("actions_needs.ns_actions_started", true)} />
                                Yes
                            </label>
                            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                                <input type="radio" name="ns-actions" className="accent-primary" checked={field("actions_needs.ns_actions_started") === "false"} onChange={() => onFieldChange?.("actions_needs.ns_actions_started", false)} />
                                No
                            </label>
                        </div>

                        <p className="text-sm text-muted-foreground">Select the actions that apply.</p>

                        <div className="relative">
                            <button
                                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                className="flex items-center justify-between w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground hover:bg-muted/50 transition-colors"
                            >
                                <span>Select action type</span>
                                <ChevronDown className={`h-4 w-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {isDropdownOpen && (
                                <div className="absolute z-10 w-full mt-1 bg-card border border-input rounded shadow-lg max-h-60 overflow-y-auto">
                                    {actionOptions.map((option) => (
                                        <button
                                            key={option}
                                            onClick={() => handleActionSelect(option)}
                                            className="w-full px-3 py-2 text-sm text-left text-foreground hover:bg-muted/50 transition-colors"
                                            disabled={selectedActions.includes(option)}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {selectedActions.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm text-muted-foreground">Selected actions:</p>
                                <div className="flex flex-wrap gap-2">
                                    {selectedActions.map((action) => (
                                        <span
                                            key={action}
                                            className="inline-flex items-center gap-1 bg-primary/10 text-primary text-xs px-2 py-1 rounded"
                                        >
                      {action}
                                            <button
                                                onClick={() => removeAction(action)}
                                                className="text-primary hover:text-primary/70 ml-1"
                                            >
                        ×
                      </button>
                    </span>
                                    ))}
                                </div>
                            </div>
                        )}
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
          <textarea rows={4} placeholder="Description" value={field("actions_needs.ifrc_description")} onChange={change("actions_needs.ifrc_description")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
        </FormField>

        <FormField
          label="Participating National Societies"
          description="Briefly set out which PNS are present and give details of PNS contributions/roles on the ground and remotely for this specific operation."
        >
          <textarea rows={4} value={field("actions_needs.participating_ns")} onChange={change("actions_needs.participating_ns")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
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
          <textarea rows={4} placeholder="Description" value={field("actions_needs.icrc_description")} onChange={change("actions_needs.icrc_description")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
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
              <input type="radio" name="gov-request" className="accent-primary" checked={field("actions_needs.gov_requested_assistance") === "true"} onChange={() => onFieldChange?.("actions_needs.gov_requested_assistance", true)} />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="gov-request" className="accent-primary" checked={field("actions_needs.gov_requested_assistance") === "false"} onChange={() => onFieldChange?.("actions_needs.gov_requested_assistance", false)} />
              No
            </label>
          </div>
        </FormField>

        <FormField label="National authorities" description="Brief description of actions taken by the national authorities.">
          <textarea rows={4} value={field("actions_needs.national_authorities_actions")} onChange={change("actions_needs.national_authorities_actions")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
        </FormField>

        <FormField label="UN or other actors" description="Brief description of actions taken by the UN or other actors.">
          <textarea rows={4} value={field("actions_needs.un_other_actors")} onChange={change("actions_needs.un_other_actors")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
        </FormField>

        <FormField label="Coordination mechanisms">
          <div className="flex items-center gap-4">
            <p className="text-sm text-foreground">Are there major coordination mechanisms in place?</p>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="coordination" className="accent-primary" checked={field("actions_needs.coordination_mechanisms") === "true"} onChange={() => onFieldChange?.("actions_needs.coordination_mechanisms", true)} />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="radio" name="coordination" className="accent-primary" checked={field("actions_needs.coordination_mechanisms") === "false"} onChange={() => onFieldChange?.("actions_needs.coordination_mechanisms", false)} />
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
            <ImageUploadButton label="Select a File" accept=".pdf,.docx,.pptx,.xlsx" />
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
            <textarea placeholder="Description" rows={5} value={field("actions_needs.identified_gaps")} onChange={change("actions_needs.identified_gaps")} className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y" />
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
