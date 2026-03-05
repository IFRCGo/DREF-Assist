import type { EnrichedFormState } from "@/lib/api";

interface ReviewSubmitPageProps {
  onBack: () => void;
  onSubmit: () => void;
  formState: EnrichedFormState;
}

const SECTIONS = [
  {
    title: "Operation Overview",
    fields: [
      { id: "operation_overview.national_society", label: "National Society" },
      { id: "operation_overview.dref_type", label: "DREF Type" },
      { id: "operation_overview.disaster_type", label: "Disaster Type" },
      { id: "operation_overview.disaster_onset", label: "Onset Type" },
      { id: "operation_overview.disaster_category", label: "Disaster Category" },
      { id: "operation_overview.country", label: "Country" },
      { id: "operation_overview.region_province", label: "Region/Province" },
      { id: "operation_overview.dref_title", label: "DREF Title" },
      { id: "operation_overview.emergency_appeal_planned", label: "Emergency Appeal Planned" },
    ],
  },
  {
    title: "Event Detail",
    fields: [
      { id: "event_detail.date_trigger_met", label: "Date Trigger Met" },
      { id: "event_detail.what_happened", label: "What Happened" },
      { id: "event_detail.total_affected_population", label: "Total Affected Population" },
      { id: "event_detail.people_in_need", label: "People in Need" },
      { id: "event_detail.estimated_male_affected", label: "Estimated Male Affected" },
      { id: "event_detail.estimated_female_affected", label: "Estimated Female Affected" },
      { id: "event_detail.estimated_girls_under_18", label: "Estimated Girls (under 18)" },
      { id: "event_detail.estimated_boys_under_18", label: "Estimated Boys (under 18)" },
    ],
  },
  {
    title: "Actions & Needs",
    fields: [
      { id: "actions_needs.ns_action_types", label: "National Society Action Types" },
      { id: "actions_needs.ns_actions_started", label: "NS Actions Started" },
      { id: "actions_needs.ifrc_description", label: "IFRC Presence/Support" },
      { id: "actions_needs.participating_ns", label: "Participating National Societies" },
      { id: "actions_needs.icrc_description", label: "ICRC Presence/Activities" },
      { id: "actions_needs.gov_requested_assistance", label: "Government Requested Assistance" },
      { id: "actions_needs.national_authorities_actions", label: "National Authorities Actions" },
      { id: "actions_needs.un_other_actors", label: "UN/Other Actors" },
      { id: "actions_needs.coordination_mechanisms", label: "Coordination Mechanisms" },
      { id: "actions_needs.identified_gaps", label: "Identified Gaps" },
    ],
  },
  {
    title: "Operation",
    fields: [
      { id: "operation.overall_objective", label: "Overall Objective" },
      { id: "operation.strategy_rationale", label: "Strategy Rationale" },
      { id: "operation.targeting_description", label: "Targeting Description" },
      { id: "operation.selection_criteria", label: "Selection Criteria" },
      { id: "operation.targeted_total", label: "Total Targeted Population" },
      { id: "operation.targeted_women", label: "Targeted Women" },
      { id: "operation.targeted_men", label: "Targeted Men" },
      { id: "operation.targeted_girls", label: "Targeted Girls (under 18)" },
      { id: "operation.targeted_boys", label: "Targeted Boys (under 18)" },
      { id: "operation.people_with_disability", label: "People with Disability" },
      { id: "operation.urban_population", label: "Urban Population" },
      { id: "operation.rural_population", label: "Rural Population" },
      { id: "operation.people_on_the_move", label: "People on the Move" },
      { id: "operation.staff_volunteers", label: "Staff/Volunteers" },
      { id: "operation.volunteer_diversity", label: "Volunteer Diversity" },
      { id: "operation.surge_personnel", label: "Surge Personnel" },
      { id: "operation.risk_analysis", label: "Risk Analysis" },
      { id: "operation.security_concerns", label: "Security Concerns" },
      { id: "operation.monitoring", label: "Monitoring" },
      { id: "operation.communication_strategy", label: "Communication Strategy" },
      { id: "operation.requested_amount_chf", label: "Requested Amount (CHF)" },
      { id: "operation.child_safeguarding_assessment", label: "Child Safeguarding Assessment" },
      { id: "operation.has_anti_fraud_policy", label: "Anti-Fraud Policy" },
      { id: "operation.has_psea_policy", label: "PSEA Policy" },
      { id: "operation.has_child_protection_policy", label: "Child Protection Policy" },
      { id: "operation.has_whistleblower_policy", label: "Whistleblower Policy" },
      { id: "operation.has_anti_harassment_policy", label: "Anti-Harassment Policy" },
    ],
  },
  {
    title: "Operational Timeframes & Contacts",
    fields: [
      { id: "timeframes_contacts.ns_application_date", label: "NS Application Date" },
      { id: "timeframes_contacts.operation_timeframe_months", label: "Operation Timeframe (months)" },
      { id: "timeframes_contacts.appeal_code", label: "Appeal Code" },
      { id: "timeframes_contacts.glide_number", label: "GLIDE Number" },
      { id: "timeframes_contacts.ns_contact_name", label: "NS Contact Name" },
      { id: "timeframes_contacts.ns_contact_title", label: "NS Contact Title" },
      { id: "timeframes_contacts.ns_contact_email", label: "NS Contact Email" },
      { id: "timeframes_contacts.ns_contact_phone", label: "NS Contact Phone" },
    ],
  },
];

function formatValue(value: unknown): string {
  if (value == null || value === "") return "";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

export default function ReviewSubmitPage({
  onBack,
  onSubmit,
  formState,
}: ReviewSubmitPageProps) {
  return (
    <section>
      <h2 className="mb-2 text-lg font-bold font-heading text-foreground">
        REVIEW YOUR APPLICATION
      </h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Please review your responses below before submitting.
      </p>

      <div className="space-y-6">
        {SECTIONS.map((section) => {
          const filledFields = section.fields.filter((f) => {
            const val = formState[f.id]?.value;
            return val != null && val !== "";
          });

          if (filledFields.length === 0) return null;

          return (
            <div
              key={section.title}
              className="rounded-lg border border-border bg-card"
            >
              <div className="border-b border-border px-4 py-3">
                <h3 className="text-sm font-semibold text-foreground">
                  {section.title}
                </h3>
              </div>
              <div className="divide-y divide-border">
                {filledFields.map((field) => {
                  const display = formatValue(formState[field.id]?.value);
                  return (
                    <div key={field.id} className="px-4 py-2.5">
                      <dt className="text-xs font-medium text-muted-foreground">
                        {field.label}
                      </dt>
                      <dd className="mt-0.5 text-sm text-foreground whitespace-pre-wrap">
                        {display}
                      </dd>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="mt-8 flex items-center justify-center gap-3">
        <button
          onClick={onBack}
          className="rounded-full border border-primary px-5 py-1 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
        >
          Back
        </button>
        <button
          onClick={onSubmit}
          className="rounded-full bg-primary px-5 py-1 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
        >
          Submit
        </button>
      </div>
    </section>
  );
}
