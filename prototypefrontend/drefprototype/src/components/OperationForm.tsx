import FormField from "@/components/FormField";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import ImageUploadButton from "./ImageUploadButton";
import { type EnrichedFormState } from "@/lib/api";

interface OperationFormProps {
  onBack: () => void;
  onContinue: () => void;
  formState?: EnrichedFormState;
  onFieldChange?: (fieldId: string, value: any) => void;
}

const getField = (formState: EnrichedFormState | undefined, fieldId: string): string => {
  const val = formState?.[fieldId]?.value;
  return val != null ? String(val) : "";
};

const OperationForm = ({ onBack, onContinue, formState, onFieldChange }: OperationFormProps) => {
  const field = (id: string) => getField(formState, id);
  const changeText = (id: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    onFieldChange?.(id, e.target.value);

  const YesNoField = ({ label, description, fieldId }: { label: string; description?: string; fieldId: string }) => (
    <FormField label={label} description={description}>
      <RadioGroup
        className="flex gap-6"
        value={field(fieldId) === "true" ? "yes" : field(fieldId) === "false" ? "no" : undefined}
        onValueChange={(v) => onFieldChange?.(fieldId, v === "yes")}
      >
        <div className="flex items-center gap-2">
          <RadioGroupItem value="yes" id={`${fieldId}-yes`} />
          <Label htmlFor={`${fieldId}-yes`} className="text-sm">Yes</Label>
        </div>
        <div className="flex items-center gap-2">
          <RadioGroupItem value="no" id={`${fieldId}-no`} />
          <Label htmlFor={`${fieldId}-no`} className="text-sm">No</Label>
        </div>
      </RadioGroup>
    </FormField>
  );

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
          placeholder="The IFRC-DREF operation aims to [primary action] in order to [desired impact] for [target population] affected by [event/disaster], by providing [key services/interventions] and ensuring [core outcomes such as protection, dignity, and resilience] over [operation period]."
          rows={4}
          value={field("operation.overall_objective")}
          onChange={changeText("operation.overall_objective")}
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
          <Textarea rows={4} value={field("operation.strategy_rationale")} onChange={changeText("operation.strategy_rationale")} />
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
        <Textarea rows={3} placeholder="Description" value={field("operation.targeting_description")} onChange={changeText("operation.targeting_description")} />
      </FormField>

      <FormField
        label="Explain the selection criteria for the targeted population"
        description="Explain the rational and logic behind which groups are being targeted and why and address vulnerable groups."
      >
        <Textarea rows={3} placeholder="Description" value={field("operation.selection_criteria")} onChange={changeText("operation.selection_criteria")} />
      </FormField>

      <FormField label="Upload any additional support document">
        <ImageUploadButton label="Upload document (Optional)" accept=".pdf,.docx,.pptx,.xlsx,image/*" />
      </FormField>

      {/* TOTAL TARGETED POPULATION */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Total Targeted Population
      </h2>

      <div className="rounded border border-border bg-card p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-semibold">Women</Label>
            <Input type="number" className="mt-1" value={field("operation.targeted_women")} onChange={changeText("operation.targeted_women")} />
          </div>
          <div>
            <Label className="text-sm font-semibold">Men</Label>
            <Input type="number" className="mt-1" value={field("operation.targeted_men")} onChange={changeText("operation.targeted_men")} />
          </div>
          <div>
            <Label className="text-sm font-semibold">Girls (under 18)</Label>
            <Input type="number" className="mt-1" value={field("operation.targeted_girls")} onChange={changeText("operation.targeted_girls")} />
          </div>
          <div>
            <Label className="text-sm font-semibold">Boys (under 18)</Label>
            <Input type="number" className="mt-1" value={field("operation.targeted_boys")} onChange={changeText("operation.targeted_boys")} />
          </div>
          <div>
            <Label className="text-sm font-semibold">Total Population</Label>
            <Input type="number" className="mt-1" value={field("operation.targeted_total")} onChange={changeText("operation.targeted_total")} />
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
            <Input type="number" className="mt-1" value={field("operation.people_with_disability")} onChange={changeText("operation.people_with_disability")} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-semibold">Urban</Label>
            <Input type="number" className="mt-1" value={field("operation.urban_population")} onChange={changeText("operation.urban_population")} />
          </div>
          <div>
            <Label className="text-sm font-semibold">Rural</Label>
            <Input type="number" className="mt-1" value={field("operation.rural_population")} onChange={changeText("operation.rural_population")} />
          </div>
        </div>
        <div>
          <Label className="text-sm font-semibold">Estimated Number of People on the move (if any)</Label>
          <Input type="number" className="mt-1" value={field("operation.people_on_the_move")} onChange={changeText("operation.people_on_the_move")} />
        </div>
      </div>

      {/* RISK AND SECURITY CONSIDERATIONS */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Risk and Security Considerations (Including "Management")
      </h2>

      <YesNoField label="Does your National Society have anti-fraud and corruption policy?" fieldId="operation.has_anti_fraud_policy" />
      <YesNoField label="Does your National Society have prevention of sexual exploitation and abuse policy?" fieldId="operation.has_psea_policy" />
      <YesNoField label="Does your National Society have child protection/child safeguarding policy?" fieldId="operation.has_child_protection_policy" />
      <YesNoField label="Does your National Society have whistleblower protection policy?" fieldId="operation.has_whistleblower_policy" />
      <YesNoField label="Does your National Society have anti-sexual harassment policy?" fieldId="operation.has_anti_harassment_policy" />

      <FormField
        label="Please analyse and indicate potential risks for this operation, its root causes and mitigation actions."
        description="When identifying the risks, please review the IFRC Risk Management Policy and Framework including the different risk categories."
      >
        <div className="space-y-2">
          <a href="#" className="text-xs text-primary underline">Annex III - Risk Categories.pdf</a>
          <Textarea rows={4} value={field("operation.risk_analysis")} onChange={changeText("operation.risk_analysis")} />
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
          <Textarea rows={4} value={field("operation.security_concerns")} onChange={changeText("operation.security_concerns")} />
        </div>
      </FormField>

      <YesNoField
        label="Has the child safeguarding risk analysis assessment been completed?"
        description="The IFRC Child Safeguarding Risk Analysis helps Operations quickly identify and rate their key child safeguarding risks."
        fieldId="operation.child_safeguarding_assessment"
      />

      {/* PLANNED INTERVENTION */}
      <h2 className="mt-6 text-lg font-bold font-heading text-foreground uppercase tracking-wide">
        Planned Intervention
      </h2>

      <FormField label="Upload your budget summary">
        <div className="space-y-2">
          <ImageUploadButton label="Upload document" accept=".pdf,.docx,.pptx,.xlsx,image/*" />
          <a href="#" className="text-xs text-primary underline">Download the Budget Template</a>
        </div>
      </FormField>

      <FormField
        label="Requested Amount in CHF"
        description="General funding requested to fund the interventions."
      >
        <Input type="number" placeholder="CHF" value={field("operation.requested_amount_chf")} onChange={changeText("operation.requested_amount_chf")} />
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
          <Textarea rows={3} placeholder="Description" value={field("operation.staff_volunteers")} onChange={changeText("operation.staff_volunteers")} />
        </div>
      </FormField>

      <FormField
        label="Does your volunteer team reflect the gender, age, and cultural diversity of the people you're helping?"
        description="This question is about making sure your team includes the right mix of people to best support those affected."
      >
        <Textarea rows={3} placeholder="Description" value={field("operation.volunteer_diversity")} onChange={changeText("operation.volunteer_diversity")} />
      </FormField>

      <YesNoField label="Will surge personnel be deployed?" fieldId="operation.surge_personnel" />

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
          <Textarea rows={3} placeholder="Description" value={field("operation.procurement")} onChange={changeText("operation.procurement")} />
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
          <Textarea rows={3} placeholder="Description" value={field("operation.monitoring")} onChange={changeText("operation.monitoring")} />
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
          <Textarea rows={3} placeholder="Description" value={field("operation.communication_strategy")} onChange={changeText("operation.communication_strategy")} />
        </div>
      </FormField>

      {/* Navigation */}
      <div className="flex items-center justify-center gap-3 pt-4">
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
    </div>
  );
};

export default OperationForm;
