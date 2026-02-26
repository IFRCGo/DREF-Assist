import FormField from "./FormField";
import { Plus, ChevronDown } from "lucide-react";
import ImageUploadButton from "./ImageUploadButton";
import { useState } from "react";
import EvaluationModal from "./EvaluationModal";

const TextArea = ({ placeholder, rows = 4 }: { placeholder?: string; rows?: number }) => (
    <textarea
        rows={rows}
        placeholder={placeholder}
        className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
    />
);

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
}

const ActionsNeedsForm = ({ onBack, onContinue }: ActionsNeedsFormProps) => {
    const [selectedActions, setSelectedActions] = useState<string[]>([]);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [ifrcDescription, setIfrcDescription] = useState("");
    const [participatingNsDescription, setParticipatingNsDescription] = useState("");
    const [icrcDescription, setIcrcDescription] = useState("");
    const [governmentRequest, setGovernmentRequest] = useState("");
    const [nationalAuthoritiesDescription, setNationalAuthoritiesDescription] = useState("");
    const [unOtherActorsDescription, setUnOtherActorsDescription] = useState("");
    const [coordinationMechanisms, setCoordinationMechanisms] = useState("");
    const [assessmentReportUploaded, setAssessmentReportUploaded] = useState(false);
    const [needsIdentified, setNeedsIdentified] = useState<string[]>([]);
    const [gapsLimitations, setGapsLimitations] = useState("");
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [evaluationResult, setEvaluationResult] = useState<any>(null);
    const [showModal, setShowModal] = useState(false);

    const handleActionSelect = (action: string) => {
        if (!selectedActions.includes(action)) {
            setSelectedActions([...selectedActions, action]);
        }
        setIsDropdownOpen(false);
    };

    const handleEvaluate = async () => {
        setIsEvaluating(true);
        setShowModal(true);
        try {
            const formData = {
                current_ns_actions: selectedActions,
                ifrc_description: ifrcDescription,
                participating_ns_description: participatingNsDescription,
                icrc_description: icrcDescription,
                government_request: governmentRequest,
                national_authorities_description: nationalAuthoritiesDescription,
                un_other_actors_description: unOtherActorsDescription,
                coordination_mechanisms: coordinationMechanisms,
                assessment_report_uploaded: assessmentReportUploaded,
                needs_identified: needsIdentified,
                gaps_limitations: gapsLimitations,
            };
            const response = await fetch(
                "http://localhost:8000/api/v2/dref-evaluation/ai-evaluate/",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ form_data: formData, section: "actions_needs" }),
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
                                <input type="radio" name="ns-actions" className="accent-primary" />
                                Yes
                            </label>
                            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                                <input type="radio" name="ns-actions" className="accent-primary" />
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
          <textarea
            rows={5}
            value={ifrcDescription}
            onChange={(e) => setIfrcDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder="Description"
          />
        </FormField>

        <FormField
          label="Participating National Societies"
          description="Briefly set out which PNS are present and give details of PNS contributions/roles on the ground and remotely for this specific operation."
        >
          <textarea
            rows={5}
            value={participatingNsDescription}
            onChange={(e) => setParticipatingNsDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder=""
          />
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
          <textarea
            rows={5}
            value={icrcDescription}
            onChange={(e) => setIcrcDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder="Description"
          />
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
              <input
                type="radio"
                name="gov-request"
                value="yes"
                checked={governmentRequest === "yes"}
                onChange={(e) => setGovernmentRequest(e.target.value)}
                className="accent-primary"
              />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="radio"
                name="gov-request"
                value="no"
                checked={governmentRequest === "no"}
                onChange={(e) => setGovernmentRequest(e.target.value)}
                className="accent-primary"
              />
              No
            </label>
          </div>
        </FormField>

        <FormField label="National authorities" description="Brief description of actions taken by the national authorities.">
          <textarea
            rows={4}
            value={nationalAuthoritiesDescription}
            onChange={(e) => setNationalAuthoritiesDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder=""
          />
        </FormField>

        <FormField label="UN or other actors" description="Brief description of actions taken by the UN or other actors.">
          <textarea
            rows={4}
            value={unOtherActorsDescription}
            onChange={(e) => setUnOtherActorsDescription(e.target.value)}
            className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder=""
          />
        </FormField>

        <FormField label="Coordination mechanisms">
          <div className="flex items-center gap-4">
            <p className="text-sm text-foreground">Are there major coordination mechanisms in place?</p>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="radio"
                name="coordination"
                value="yes"
                checked={coordinationMechanisms === "yes"}
                onChange={(e) => setCoordinationMechanisms(e.target.value)}
                className="accent-primary"
              />
              Yes
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="radio"
                name="coordination"
                value="no"
                checked={coordinationMechanisms === "no"}
                onChange={(e) => setCoordinationMechanisms(e.target.value)}
                className="accent-primary"
              />
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
            <button
              onClick={() => setAssessmentReportUploaded(!assessmentReportUploaded)}
              className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              {assessmentReportUploaded ? "✓ Report Uploaded" : "Select a File"}
            </button>
            {assessmentReportUploaded && <span className="text-xs text-green-600 ml-2">Report uploaded</span>}
          </div>
        </FormField>

        <FormField label="Needs identified">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Enter identified needs (comma-separated or as items).</p>
            <textarea
              rows={3}
              value={needsIdentified.join(", ")}
              onChange={(e) => setNeedsIdentified(e.target.value.split(",").map(s => s.trim()).filter(s => s))}
              className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
              placeholder="e.g. Shelter, Water & Sanitation, Health"
            />
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
            <textarea
              rows={5}
              value={gapsLimitations}
              onChange={(e) => setGapsLimitations(e.target.value)}
              className="w-full rounded border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
              placeholder="Description"
            />
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
          current_ns_actions: selectedActions,
          ifrc_description: ifrcDescription,
          participating_ns_description: participatingNsDescription,
          icrc_description: icrcDescription,
          government_request: governmentRequest,
          national_authorities_description: nationalAuthoritiesDescription,
          un_other_actors_description: unOtherActorsDescription,
          coordination_mechanisms: coordinationMechanisms,
          assessment_report_uploaded: assessmentReportUploaded,
          needs_identified: needsIdentified,
          gaps_limitations: gapsLimitations,
        }}
      />
    </section>
  );
};

export default ActionsNeedsForm;
