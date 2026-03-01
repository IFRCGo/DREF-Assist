export const FIELD_LABELS: Record<string, string> = {
  "operation_overview.national_society": "National Society",
  "operation_overview.dref_type": "DREF Type",
  "operation_overview.disaster_type": "Disaster Type",
  "operation_overview.disaster_onset": "Onset Type",
  "operation_overview.disaster_category": "Disaster Category",
  "operation_overview.country": "Country",
  "operation_overview.region_province": "Region/Province",
  "operation_overview.dref_title": "DREF Title",
  "operation_overview.emergency_appeal_planned": "Emergency Appeal Planned",
  "event_detail.date_trigger_met": "Date Trigger Met",
  "event_detail.total_affected_population": "Total Affected Population",
  "event_detail.people_in_need": "People in Need",
  "event_detail.estimated_male_affected": "Estimated Male Affected",
  "event_detail.estimated_female_affected": "Estimated Female Affected",
  "event_detail.estimated_girls_under_18": "Estimated Girls (under 18)",
  "event_detail.estimated_boys_under_18": "Estimated Boys (under 18)",
  "event_detail.what_happened": "What Happened",
};

export function getFieldLabel(fieldId: string): string {
  return FIELD_LABELS[fieldId] ?? fieldId;
}
