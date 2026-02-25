# Field Update Approval Mechanism

**Date:** 2026-02-25
**Status:** Approved

## Problem

When the DREF Assist AI suggests field changes, they are auto-applied immediately. Users have no way to review, accept, or reject individual changes before they take effect.

## Solution

Cursor-style inline approval cards in the chat. Each assistant message with field updates shows a card listing every proposed change with per-field accept/reject buttons and bulk Accept All / Reject All actions.

## Behavior

1. **LLM returns field_updates** → stored as "pending" (not applied to form)
2. **User accepts** a change → applied to formState, marked green in UI
3. **User rejects** a change → not applied, shown struck-through in UI
4. **Accept All / Reject All** → bulk action on all pending changes in that message
5. **User sends next prompt without acting** → all pending changes auto-accepted before the message is sent
6. **Rejected changes** remain visible (struck through) as audit trail

## Data Model

```typescript
type FieldUpdateStatus = "pending" | "accepted" | "rejected";

interface TrackedFieldUpdate {
  update: FieldUpdate;
  status: FieldUpdateStatus;
}

// State in DREFAssistChat: keyed by message ID, then by field_id
pendingUpdates: Map<string, Map<string, TrackedFieldUpdate>>
```

## UI Layout

Inside each assistant message that has field updates:

```
┌─────────────────────────────────────┐
│ N suggested changes  [✓ All] [✗ All]│
├─────────────────────────────────────┤
│ Disaster Type: Earthquake    [✓] [✗]│
│ Country: Philippines         [✓] [✗]│
│ Onset Type: Sudden           [✓] [✗]│
└─────────────────────────────────────┘
```

### States

- **Pending:** Normal text, accept/reject buttons visible
- **Accepted:** Green text + checkmark icon, buttons removed
- **Rejected:** Struck-through muted text + X icon, buttons removed

### Bulk actions

- Accept All / Reject All toolbar at top of card
- Hidden once all changes in that message are resolved

## Field Label Mapping

A constant mapping from field_id to human-readable label:

```typescript
const FIELD_LABELS: Record<string, string> = {
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
```

## Auto-Accept on Next Prompt

In `sendMessage()`, before sending the API request:
1. Iterate all entries in `pendingUpdates`
2. For any with status "pending", set to "accepted"
3. Call `onFieldUpdates` with the newly accepted updates
4. Then proceed with sending the message

## Files Changed

- **DREFAssistChat.tsx** — Remove auto-apply, add pending state, render approval cards, auto-accept logic
- **New: fieldLabels.ts** — FIELD_LABELS constant
- **No backend changes**
- **No changes to Index.tsx** (onFieldUpdates callback unchanged)
