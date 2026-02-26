import FormField from "@/components/FormField";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import ImageUploadButton from "./ImageUploadButton";
import EvaluationModal from "./EvaluationModal";
import { useState } from "react";

interface OperationFormProps {
  onBack: () => void;
  onContinue: () => void;
}

const YesNoField = ({ label, description }: { label: string; description?: string }) => (
  <FormField label={label} description={description}>
    <RadioGroup className="flex gap-6">
      <div className="flex items-center gap-2">
        <RadioGroupItem value="yes" id={`${label}-yes`} />
        <Label htmlFor={`${label}-yes`} className="text-sm">Yes</Label>
      </div>
      <div className="flex items-center gap-2">
        <RadioGroupItem value="no" id={`${label}-no`} />
        <Label htmlFor={`${label}-no`} className="text-sm">No</Label>
      </div>
    </RadioGroup>
  </FormField>
);

const OperationForm = ({ onBack, onContinue }: OperationFormProps) => {
  // Form state - Objective and Strategy
  const [operationObjective, setOperationObjective] = useState("");
  const [operationStrategyRationale, setOperationStrategyRationale] = useState("");
  
  // Targeting Strategy
  const [targetingDescription, setTargetingDescription] = useState("");
  const [selectionCriteria, setSelectionCriteria] = useState("");
  const [supportDocumentUploaded, setSupportDocumentUploaded] = useState(false);
  
  // Total Targeted Population
  const [womenTargeted, setWomenTargeted] = useState("");
  const [menTargeted, setMenTargeted] = useState("");
  const [girlsTargeted, setGirlsTargeted] = useState("");
  const [boysTargeted, setBoysTargeted] = useState("");
  
  // Risk and Security
  const [antifraudPolicy, setAntifraudPolicy] = useState("");
  const [sexualExploitationPolicy, setSexualExploitationPolicy] = useState("");
  const [childProtectionPolicy, setChildProtectionPolicy] = useState("");
  const [whistleblowerPolicy, setWhistleblowerPolicy] = useState("");
  const [antiHarassmentPolicy, setAntiHarassmentPolicy] = useState("");
  const [riskAnalysis, setRiskAnalysis] = useState("");
  const [securityConcerns, setSecurityConcerns] = useState("");
  const [childSafeguardingAssessment, setChildSafeguardingAssessment] = useState("");
  
  // Planned Intervention
  const [budgetUploaded, setBudgetUploaded] = useState(false);
  const [requestedAmount, setRequestedAmount] = useState("");
  
  // Support Services
  const [staffVolunteersDescription, setStaffVolunteersDescription] = useState("");
  const [volunteerDiversityDescription, setVolunteerDiversityDescription] = useState("");
  const [surgePersonnelDeployed, setSurgePersonnelDeployed] = useState("");
  const [procurementDescription, setProcurementDescription] = useState("");
  const [monitoringDescription, setMonitoringDescription] = useState("");
  const [communicationStrategy, setCommunicationStrategy] = useState("");
  
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    setShowModal(true);
    try {
      const formData = {
        operation_objective: operationObjective,
        operation_strategy_rationale: operationStrategyRationale,
        targeting_description: targetingDescription,
        selection_criteria: selectionCriteria,
        support_document_uploaded: supportDocumentUploaded,
        women_targeted: womenTargeted,
        men_targeted: menTargeted,
        girls_targeted: girlsTargeted,
        boys_targeted: boysTargeted,
        antifraud_policy: antifraudPolicy,
        sexual_exploitation_policy: sexualExploitationPolicy,
        child_protection_policy: childProtectionPolicy,
        whistleblower_policy: whistleblowerPolicy,
        anti_harassment_policy: antiHarassmentPolicy,
        risk_analysis: riskAnalysis,
        security_concerns: securityConcerns,
        child_safeguarding_assessment: childSafeguardingAssessment,
        budget_uploaded: budgetUploaded,
        requested_amount: requestedAmount,
        staff_volunteers_description: staffVolunteersDescription,
        volunteer_diversity_description: volunteerDiversityDescription,
        surge_personnel_deployed: surgePersonnelDeployed,
        procurement_description: procurementDescription,
        monitoring_description: monitoringDescription,
        communication_strategy: communicationStrategy,
      };

      const response = await fetch(
        "http://localhost:8000/api/v2/dref-evaluation/ai-evaluate/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            form_data: formData,
            section: "operation",
          }),
        }
      );

      const result = await response.json();
      setEvaluationResult(result);
    } catch (error) {
      console.error("Evaluation error:", error);
      setEvaluationResult({
        error: `Failed to evaluate: ${(error as Error).message}`,
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-6 pb-8">
      {/* OBJECTIVE AND STRATEGY RATIONALE */}
      <h2 className="mt-4 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Objective and Strategy Rationale
      </h2>

      <FormField
        label="Overall objective of the operation"
        description="The objective statement should clearly and concisely describe the primary goal of the operation, focusing on the humanitarian impact."
      >
        <Textarea
          value={operationObjective}
          onChange={(e) => setOperationObjective(e.target.value)}
          placeholder="The IFRC-DREF operation aims to [primary action] in order to [desired impact] for [target population] affected by [event/disaster], by providing [key services/interventions] and ensuring [core outcomes such as protection, dignity, and resilience] over [operation period]."
          rows={4}
        />
      </FormField>

      <FormField
        label="Operation strategy rationale"
        description="Elaborate on the overall plan, strategy and approach of the operation; explain the reasoning behind the chosen strategy for the emergency operation."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>Highlight the most urgent needs the operation aims to address.</li>
            <li>Describe the main priorities and explain why these priorities were chosen.</li>
            <li>Justify why particular methods and actions were selected.</li>
            <li>Include any key factors that influence the strategy.</li>
          </ul>
          <Textarea
            value={operationStrategyRationale}
            onChange={(e) => setOperationStrategyRationale(e.target.value)}
            rows={4}
          />
        </div>
      </FormField>

      {/* TARGETING STRATEGY */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Targeting Strategy
      </h2>

      <FormField
        label="Who will be targeted through this operation?"
        description="Explain the logic behind our targets. Which groups are we targeting and why? Explain how you will target vulnerable groups (e.g., Migrants, refugees, etc.)"
      >
        <Textarea
          value={targetingDescription}
          onChange={(e) => setTargetingDescription(e.target.value)}
          rows={3}
          placeholder="Description"
        />
      </FormField>

      <FormField
        label="Explain the selection criteria for the targeted population"
        description="Explain the rational and logic behind which groups are being targeted and why and address vulnerable groups."
      >
        <Textarea
          value={selectionCriteria}
          onChange={(e) => setSelectionCriteria(e.target.value)}
          rows={3}
          placeholder="Description"
        />
      </FormField>

      <FormField label="Upload any additional support document">
        <button
          onClick={() => setSupportDocumentUploaded(!supportDocumentUploaded)}
          className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
        >
          {supportDocumentUploaded ? "✓ Document Uploaded" : "Upload document (Optional)"}
        </button>
        {supportDocumentUploaded && <span className="text-xs text-green-600 ml-2">Document uploaded</span>}
      </FormField>

      {/* TOTAL TARGETED POPULATION */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Total Targeted Population
      </h2>

      <div className="rounded border border-border bg-card p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-semibold">Women</Label>
            <Input
              type="number"
              value={womenTargeted}
              onChange={(e) => setWomenTargeted(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm font-semibold">Men</Label>
            <Input
              type="number"
              value={menTargeted}
              onChange={(e) => setMenTargeted(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm font-semibold">Girls (under 18)</Label>
            <Input
              type="number"
              value={girlsTargeted}
              onChange={(e) => setGirlsTargeted(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm font-semibold">Boys (under 18)</Label>
            <Input
              type="number"
              value={boysTargeted}
              onChange={(e) => setBoysTargeted(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm font-semibold">Total Population</Label>
            <Input type="number" className="mt-1" disabled />
          </div>
          <div>
            <Label className="text-sm font-semibold">Estimate</Label>
            <Input type="number" className="mt-1" />
          </div>
          <div>
            <Label className="text-sm font-semibold">Estimated Percentage</Label>
            <Input type="number" className="mt-1" placeholder="%" />
          </div>
          <div>
            <Label className="text-sm font-semibold">People with Disability</Label>
            <Input type="number" className="mt-1" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-semibold">Urban</Label>
            <Input type="number" className="mt-1" />
          </div>
          <div>
            <Label className="text-sm font-semibold">Rural</Label>
            <Input type="number" className="mt-1" />
          </div>
        </div>
        <div>
          <Label className="text-sm font-semibold">Estimated Number of People on the move (if any)</Label>
          <Input type="number" className="mt-1" />
        </div>
      </div>

      {/* RISK AND SECURITY CONSIDERATIONS */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Risk and Security Considerations (Including "Management")
      </h2>

      <FormField label="Does your National Society have anti-fraud and corruption policy?">
        <RadioGroup value={antifraudPolicy} onValueChange={setAntifraudPolicy} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="antifraud-yes" />
            <Label htmlFor="antifraud-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="antifraud-no" />
            <Label htmlFor="antifraud-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>
      <FormField label="Does your National Society have prevention of sexual exploitation and abuse policy?">
        <RadioGroup value={sexualExploitationPolicy} onValueChange={setSexualExploitationPolicy} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="sexual-yes" />
            <Label htmlFor="sexual-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="sexual-no" />
            <Label htmlFor="sexual-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>
      <FormField label="Does your National Society have child protection/child safeguarding policy?">
        <RadioGroup value={childProtectionPolicy} onValueChange={setChildProtectionPolicy} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="child-yes" />
            <Label htmlFor="child-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="child-no" />
            <Label htmlFor="child-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>
      <FormField label="Does your National Society have whistleblower protection policy?">
        <RadioGroup value={whistleblowerPolicy} onValueChange={setWhistleblowerPolicy} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="whistle-yes" />
            <Label htmlFor="whistle-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="whistle-no" />
            <Label htmlFor="whistle-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>
      <FormField label="Does your National Society have anti-sexual harassment policy?">
        <RadioGroup value={antiHarassmentPolicy} onValueChange={setAntiHarassmentPolicy} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="harassment-yes" />
            <Label htmlFor="harassment-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="harassment-no" />
            <Label htmlFor="harassment-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>

      <FormField
        label="Please analyse and indicate potential risks for this operation, its root causes and mitigation actions."
        description="When identifying the risks, please review the IFRC Risk Management Policy and Framework including the different risk categories."
      >
        <div className="space-y-2">
          <a href="#" className="text-xs text-primary underline">Annex III - Risk Categories.pdf</a>
          <Textarea
            value={riskAnalysis}
            onChange={(e) => setRiskAnalysis(e.target.value)}
            rows={4}
          />
        </div>
      </FormField>

      <FormField
        label="Please indicate any security and safety concerns for this operation."
        description="Describe any specific security or safety threats that could impact the safety of personnel, volunteers, and communities during the operation."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>Are there any security concerns related to the areas where the operation will take place?</li>
            <li>What safety risks could impact the well-being of staff, volunteers, or beneficiaries?</li>
            <li>Are there any specific security protocols or measures that need to be established?</li>
          </ul>
          <Textarea
            value={securityConcerns}
            onChange={(e) => setSecurityConcerns(e.target.value)}
            rows={4}
          />
        </div>
      </FormField>

      <FormField
        label="Has the child safeguarding risk analysis assessment been completed?"
        description="The IFRC Child Safeguarding Risk Analysis helps Operations quickly identify and rate their key child safeguarding risks."
      >
        <RadioGroup value={childSafeguardingAssessment} onValueChange={setChildSafeguardingAssessment} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="safeguarding-yes" />
            <Label htmlFor="safeguarding-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="safeguarding-no" />
            <Label htmlFor="safeguarding-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>

      {/* PLANNED INTERVENTION */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Planned Intervention
      </h2>

      <FormField label="Upload your budget summary">
        <div className="space-y-2">
          <button
            onClick={() => setBudgetUploaded(!budgetUploaded)}
            className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
          >
            {budgetUploaded ? "✓ Budget Uploaded" : "Upload document"}
          </button>
          {budgetUploaded && <span className="text-xs text-green-600">Budget uploaded</span>}
          <a href="#" className="text-xs text-primary underline">Download the Budget Template</a>
        </div>
      </FormField>

      <FormField
        label="Requested Amount in CHF"
        description="General funding requested to fund the interventions."
      >
        <Input
          type="number"
          value={requestedAmount}
          onChange={(e) => setRequestedAmount(e.target.value)}
          placeholder="CHF"
        />
        <p className="mt-1 text-xs text-destructive">Total amount of planned budget does not match the Requested Amount</p>
      </FormField>

      {/* ABOUT SUPPORT SERVICES */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        About Support Services
      </h2>

      <FormField
        label="How many staff and volunteers will be involved in this operation?"
        description="A brief description of the human resources that will be engaged in the operation, including both staff and volunteers."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>How many staff members and volunteers are expected to participate?</li>
            <li>What specific roles or responsibilities will they have?</li>
            <li>Are there any key leadership positions or coordinators overseeing the activities?</li>
          </ul>
          <Textarea
            value={staffVolunteersDescription}
            onChange={(e) => setStaffVolunteersDescription(e.target.value)}
            rows={3}
            placeholder="Description"
          />
        </div>
      </FormField>

      <FormField
        label="Does your volunteer team reflect the gender, age, and cultural diversity of the people you're helping?"
        description="This question is about making sure your team includes the right mix of people to best support those affected."
      >
        <Textarea
          value={volunteerDiversityDescription}
          onChange={(e) => setVolunteerDiversityDescription(e.target.value)}
          rows={3}
          placeholder="Description"
        />
      </FormField>

      <FormField label="Will surge personnel be deployed?">
        <RadioGroup value={surgePersonnelDeployed} onValueChange={setSurgePersonnelDeployed} className="flex gap-6">
          <div className="flex items-center gap-2">
            <RadioGroupItem value="yes" id="surge-yes" />
            <Label htmlFor="surge-yes" className="text-sm">Yes</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="no" id="surge-no" />
            <Label htmlFor="surge-no" className="text-sm">No</Label>
          </div>
        </RadioGroup>
      </FormField>

      <FormField
        label="If there is procurement, will it be done by National Society or IFRC?"
        description="Explain the responsibility for procurement activities during the operation."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>Who will be responsible for procurement (National Society or IFRC)?</li>
            <li>Will procurement involve local or international suppliers?</li>
            <li>Will it be for replenishment or for distribution?</li>
            <li>If for distribution, how long is the tendering expected to take?</li>
            <li>For Cash and Voucher Assistance, what is the status of the Financial Service Provider?</li>
          </ul>
          <Textarea
            value={procurementDescription}
            onChange={(e) => setProcurementDescription(e.target.value)}
            rows={3}
            placeholder="Description"
          />
        </div>
      </FormField>

      <FormField
        label="How will this operation be monitored?"
        description="Describe the mechanisms that will be used to track the progress and effectiveness of the operation."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>What systems will be used to monitor the operation's activities and outcomes?</li>
            <li>How will progress be tracked, and who will be responsible?</li>
            <li>What indicators or milestones will be used to assess the success?</li>
            <li>Will there be IFRC monitoring visits? How will it be deployed?</li>
          </ul>
          <Textarea
            value={monitoringDescription}
            onChange={(e) => setMonitoringDescription(e.target.value)}
            rows={3}
            placeholder="Description"
          />
        </div>
      </FormField>

      <FormField
        label="Please briefly explain the National Society's communication strategy for this operation."
        description="Describe how the National Society will manage internal and external communication throughout the operation."
      >
        <div className="space-y-2">
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
            <li>What communication channels will be used to share information internally and externally?</li>
            <li>How will the National Society ensure transparent and effective communication with the affected communities?</li>
            <li>Is there a media strategy in place for external communication?</li>
            <li>Will the IFRC be supporting with communication? What roles will be involved?</li>
          </ul>
          <Textarea
            value={communicationStrategy}
            onChange={(e) => setCommunicationStrategy(e.target.value)}
            rows={3}
            placeholder="Description"
          />
        </div>
      </FormField>

      {/* Navigation */}
      <div className="flex items-center justify-center gap-3 pt-4">
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
          operation_objective: operationObjective,
          operation_strategy_rationale: operationStrategyRationale,
          targeting_description: targetingDescription,
          selection_criteria: selectionCriteria,
          support_document_uploaded: supportDocumentUploaded,
          women_targeted: womenTargeted,
          men_targeted: menTargeted,
          girls_targeted: girlsTargeted,
          boys_targeted: boysTargeted,
          antifraud_policy: antifraudPolicy,
          sexual_exploitation_policy: sexualExploitationPolicy,
          child_protection_policy: childProtectionPolicy,
          whistleblower_policy: whistleblowerPolicy,
          anti_harassment_policy: antiHarassmentPolicy,
          risk_analysis: riskAnalysis,
          security_concerns: securityConcerns,
          child_safeguarding_assessment: childSafeguardingAssessment,
          budget_uploaded: budgetUploaded,
          requested_amount: requestedAmount,
          staff_volunteers_description: staffVolunteersDescription,
          volunteer_diversity_description: volunteerDiversityDescription,
          surge_personnel_deployed: surgePersonnelDeployed,
          procurement_description: procurementDescription,
          monitoring_description: monitoringDescription,
          communication_strategy: communicationStrategy,
        }}
      />
    </div>
  );
};

export default OperationForm;
