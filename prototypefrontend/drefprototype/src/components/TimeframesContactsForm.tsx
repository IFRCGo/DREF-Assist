import FormField from "@/components/FormField";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import EvaluationModal from "./EvaluationModal";

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
  // Timeframes
  const [nsApplicationDate, setNsApplicationDate] = useState("");
  const [gvaSubmissionDate, setGvaSubmissionDate] = useState("");
  const [approvalDate, setApprovalDate] = useState("");
  const [operationTimeframe, setOperationTimeframe] = useState("");
  const [operationEndDate, setOperationEndDate] = useState("");
  const [publishingDate, setPublishingDate] = useState("");
  
  // Tracking Data
  const [appealCode, setAppealCode] = useState("");
  const [glideNumber, setGlideNumber] = useState("");
  
  // Contacts
  const [ifrcAppealManagerName, setIfrcAppealManagerName] = useState("");
  const [ifrcAppealManagerTitle, setIfrcAppealManagerTitle] = useState("");
  const [ifrcAppealManagerEmail, setIfrcAppealManagerEmail] = useState("");
  const [ifrcAppealManagerPhone, setIfrcAppealManagerPhone] = useState("");
  
  const [ifrcProjectManagerName, setIfrcProjectManagerName] = useState("");
  const [ifrcProjectManagerTitle, setIfrcProjectManagerTitle] = useState("");
  const [ifrcProjectManagerEmail, setIfrcProjectManagerEmail] = useState("");
  const [ifrcProjectManagerPhone, setIfrcProjectManagerPhone] = useState("");
  
  const [nsContactName, setNsContactName] = useState("");
  const [nsContactTitle, setNsContactTitle] = useState("");
  const [nsContactEmail, setNsContactEmail] = useState("");
  const [nsContactPhone, setNsContactPhone] = useState("");
  
  const [ifrcFocalPointName, setIfrcFocalPointName] = useState("");
  const [ifrcFocalPointTitle, setIfrcFocalPointTitle] = useState("");
  const [ifrcFocalPointEmail, setIfrcFocalPointEmail] = useState("");
  const [ifrcFocalPointPhone, setIfrcFocalPointPhone] = useState("");
  
  const [drefFocalPointName, setDrefFocalPointName] = useState("");
  const [drefFocalPointTitle, setDrefFocalPointTitle] = useState("");
  const [drefFocalPointEmail, setDrefFocalPointEmail] = useState("");
  const [drefFocalPointPhone, setDrefFocalPointPhone] = useState("");
  
  const [mediaContactName, setMediaContactName] = useState("");
  const [mediaContactTitle, setMediaContactTitle] = useState("");
  const [mediaContactEmail, setMediaContactEmail] = useState("");
  const [mediaContactPhone, setMediaContactPhone] = useState("");
  
  const [integrityFocalPointName, setIntegrityFocalPointName] = useState("");
  const [integrityFocalPointTitle, setIntegrityFocalPointTitle] = useState("");
  const [integrityFocalPointEmail, setIntegrityFocalPointEmail] = useState("");
  const [integrityFocalPointPhone, setIntegrityFocalPointPhone] = useState("");
  
  const [nsHotline, setNsHotline] = useState("");
  
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    setShowModal(true);
    try {
      const formData = {
        ns_application_date: nsApplicationDate,
        gva_submission_date: gvaSubmissionDate,
        approval_date: approvalDate,
        operation_timeframe: operationTimeframe,
        operation_end_date: operationEndDate,
        publishing_date: publishingDate,
        appeal_code: appealCode,
        glide_number: glideNumber,
        ifrc_appeal_manager: { name: ifrcAppealManagerName, title: ifrcAppealManagerTitle, email: ifrcAppealManagerEmail, phone: ifrcAppealManagerPhone },
        ifrc_project_manager: { name: ifrcProjectManagerName, title: ifrcProjectManagerTitle, email: ifrcProjectManagerEmail, phone: ifrcProjectManagerPhone },
        ns_contact: { name: nsContactName, title: nsContactTitle, email: nsContactEmail, phone: nsContactPhone },
        ifrc_focal_point: { name: ifrcFocalPointName, title: ifrcFocalPointTitle, email: ifrcFocalPointEmail, phone: ifrcFocalPointPhone },
        dref_focal_point: { name: drefFocalPointName, title: drefFocalPointTitle, email: drefFocalPointEmail, phone: drefFocalPointPhone },
        media_contact: { name: mediaContactName, title: mediaContactTitle, email: mediaContactEmail, phone: mediaContactPhone },
        integrity_focal_point: { name: integrityFocalPointName, title: integrityFocalPointTitle, email: integrityFocalPointEmail, phone: integrityFocalPointPhone },
        ns_hotline: nsHotline,
      };
      const response = await fetch(
        "http://localhost:8000/api/v2/dref-evaluation/ai-evaluate/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ form_data: formData, section: "operational_timeframe_contacts" }),
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

  return (
    <div className="space-y-6 py-4">
      {/* ── OPERATIONAL TIMEFRAMES ── */}
      <h2 className="text-lg font-bold text-foreground">Operational Timeframes</h2>

      <FormField label="Date of National Society Application">
        <Input type="date" value={nsApplicationDate} onChange={(e) => setNsApplicationDate(e.target.value)} />
      </FormField>

      <FormField label="Date of Submission to GVA" description="Added by Regional Office">
        <Input type="date" value={gvaSubmissionDate} onChange={(e) => setGvaSubmissionDate(e.target.value)} />
      </FormField>

      <FormField label="Date of Approval">
        <Input type="date" value={approvalDate} onChange={(e) => setApprovalDate(e.target.value)} />
      </FormField>

      <FormField label="Operation timeframe (months)">
        <Input
          type="number"
          placeholder="Input number of months"
          min={1}
          value={operationTimeframe}
          onChange={(e) => setOperationTimeframe(e.target.value)}
        />
      </FormField>

      <FormField
        label="End date of Operation"
        description="Automatically calculated using the Date of Approval + Operation timeframe"
      >
        <Input type="date" value={operationEndDate} onChange={(e) => setOperationEndDate(e.target.value)} />
      </FormField>

      <FormField label="Date of Publishing" description="Added by Regional Office">
        <Input type="date" value={publishingDate} onChange={(e) => setPublishingDate(e.target.value)} />
      </FormField>

      {/* ── STAGING SITE ── */}
      <h2 className="text-lg font-bold text-foreground">Staging Site</h2>
      {/* placeholder – no fields visible in the PDF for this section */}

      {/* ── TRACKING DATA AND CONTACTS ── */}
      <h2 className="text-lg font-bold text-foreground">Tracking Data and Contacts</h2>

      <FormField label="Appeal Code" description="Added by the regional PMER">
        <Input placeholder="Appeal Code" value={appealCode} onChange={(e) => setAppealCode(e.target.value)} />
      </FormField>

      <FormField label="GLIDE number">
        <Input placeholder="GLIDE number" value={glideNumber} onChange={(e) => setGlideNumber(e.target.value)} />
      </FormField>

      <FormField label="IFRC Appeal Manager" description="Added by the regional office">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={ifrcAppealManagerName} onChange={(e) => setIfrcAppealManagerName(e.target.value)} />
          <Input placeholder="Title" value={ifrcAppealManagerTitle} onChange={(e) => setIfrcAppealManagerTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={ifrcAppealManagerEmail} onChange={(e) => setIfrcAppealManagerEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={ifrcAppealManagerPhone} onChange={(e) => setIfrcAppealManagerPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="IFRC Project Manager" description="Added by the regional office">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={ifrcProjectManagerName} onChange={(e) => setIfrcProjectManagerName(e.target.value)} />
          <Input placeholder="Title" value={ifrcProjectManagerTitle} onChange={(e) => setIfrcProjectManagerTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={ifrcProjectManagerEmail} onChange={(e) => setIfrcProjectManagerEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={ifrcProjectManagerPhone} onChange={(e) => setIfrcProjectManagerPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="National Society Contact">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={nsContactName} onChange={(e) => setNsContactName(e.target.value)} />
          <Input placeholder="Title" value={nsContactTitle} onChange={(e) => setNsContactTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={nsContactEmail} onChange={(e) => setNsContactEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={nsContactPhone} onChange={(e) => setNsContactPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="IFRC Focal Point for the Emergency">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={ifrcFocalPointName} onChange={(e) => setIfrcFocalPointName(e.target.value)} />
          <Input placeholder="Title" value={ifrcFocalPointTitle} onChange={(e) => setIfrcFocalPointTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={ifrcFocalPointEmail} onChange={(e) => setIfrcFocalPointEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={ifrcFocalPointPhone} onChange={(e) => setIfrcFocalPointPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="DREF Regional Focal Point">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={drefFocalPointName} onChange={(e) => setDrefFocalPointName(e.target.value)} />
          <Input placeholder="Title" value={drefFocalPointTitle} onChange={(e) => setDrefFocalPointTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={drefFocalPointEmail} onChange={(e) => setDrefFocalPointEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={drefFocalPointPhone} onChange={(e) => setDrefFocalPointPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="Media Contact">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={mediaContactName} onChange={(e) => setMediaContactName(e.target.value)} />
          <Input placeholder="Title" value={mediaContactTitle} onChange={(e) => setMediaContactTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={mediaContactEmail} onChange={(e) => setMediaContactEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={mediaContactPhone} onChange={(e) => setMediaContactPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="National Societies' Integrity Focal Point">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input placeholder="Name" value={integrityFocalPointName} onChange={(e) => setIntegrityFocalPointName(e.target.value)} />
          <Input placeholder="Title" value={integrityFocalPointTitle} onChange={(e) => setIntegrityFocalPointTitle(e.target.value)} />
          <Input placeholder="Email" type="email" value={integrityFocalPointEmail} onChange={(e) => setIntegrityFocalPointEmail(e.target.value)} />
          <Input placeholder="Phone Number" type="tel" value={integrityFocalPointPhone} onChange={(e) => setIntegrityFocalPointPhone(e.target.value)} />
        </div>
      </FormField>

      <FormField label="National Society Hotline">
        <Input placeholder="Phone Number" type="tel" value={nsHotline} onChange={(e) => setNsHotline(e.target.value)} />
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
          ns_application_date: nsApplicationDate,
          gva_submission_date: gvaSubmissionDate,
          approval_date: approvalDate,
          operation_timeframe: operationTimeframe,
          operation_end_date: operationEndDate,
          publishing_date: publishingDate,
          appeal_code: appealCode,
          glide_number: glideNumber,
          ifrc_appeal_manager: { name: ifrcAppealManagerName, title: ifrcAppealManagerTitle, email: ifrcAppealManagerEmail, phone: ifrcAppealManagerPhone },
          ifrc_project_manager: { name: ifrcProjectManagerName, title: ifrcProjectManagerTitle, email: ifrcProjectManagerEmail, phone: ifrcProjectManagerPhone },
          ns_contact: { name: nsContactName, title: nsContactTitle, email: nsContactEmail, phone: nsContactPhone },
          ifrc_focal_point: { name: ifrcFocalPointName, title: ifrcFocalPointTitle, email: ifrcFocalPointEmail, phone: ifrcFocalPointPhone },
          dref_focal_point: { name: drefFocalPointName, title: drefFocalPointTitle, email: drefFocalPointEmail, phone: drefFocalPointPhone },
          media_contact: { name: mediaContactName, title: mediaContactTitle, email: mediaContactEmail, phone: mediaContactPhone },
          integrity_focal_point: { name: integrityFocalPointName, title: integrityFocalPointTitle, email: integrityFocalPointEmail, phone: integrityFocalPointPhone },
          ns_hotline: nsHotline,
        }}
      />
    </div>
  );
};

export default TimeframesContactsForm;
