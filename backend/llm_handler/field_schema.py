from datetime import datetime
from typing import List, Dict, Any, Optional

# Define valid field IDs based on the specification
VALID_FIELD_IDS = {
    # operation_overview
    "operation_overview.national_society",
    "operation_overview.dref_type",
    "operation_overview.disaster_type",
    "operation_overview.disaster_onset",
    "operation_overview.disaster_category",
    "operation_overview.country",
    "operation_overview.region_province",
    "operation_overview.dref_title",
    "operation_overview.emergency_appeal_planned",
    
    # event_detail
    "event_detail.date_trigger_met",
    "event_detail.total_affected_population",
    "event_detail.people_in_need",
    "event_detail.estimated_male_affected",
    "event_detail.estimated_female_affected",
    "event_detail.estimated_girls_under_18",
    "event_detail.estimated_boys_under_18",
    "event_detail.what_happened",
}

FIELD_TYPES = {
    "operation_overview.national_society": "dropdown",
    "operation_overview.dref_type": "dropdown",
    "operation_overview.disaster_type": "dropdown",
    "operation_overview.disaster_onset": "dropdown",
    "operation_overview.disaster_category": "dropdown",
    "operation_overview.country": "dropdown",
    "operation_overview.region_province": "text",
    "operation_overview.dref_title": "text",
    "operation_overview.emergency_appeal_planned": "boolean",
    
    "event_detail.date_trigger_met": "date",
    "event_detail.total_affected_population": "number",
    "event_detail.people_in_need": "number",
    "event_detail.estimated_male_affected": "number",
    "event_detail.estimated_female_affected": "number",
    "event_detail.estimated_girls_under_18": "number",
    "event_detail.estimated_boys_under_18": "number",
    "event_detail.what_happened": "text",
}

DROPDOWN_OPTIONS = {
    "operation_overview.dref_type": ["Imminent Crisis", "Response", "Protracted Crisis"],
    "operation_overview.disaster_onset": ["Sudden", "Slow"],
    "operation_overview.disaster_category": ["Yellow", "Orange", "Red"],
    "operation_overview.disaster_type": [
        "Flood", "Earthquake", "Epidemic", "Cyclone", "Drought", "Fire", 
        "Landslide", "Tsunami", "Volcanic Eruption", "Civil Unrest", 
        "Population Movement", "Other"
    ],
    # Lists of countries and societies would typically be dynamic or much longer.
    # For this implementation, we allow any value validation logic or placeholder
    # assuming the system prompt provides the lists or we validate loosely if logic requires.
    # However, strict validation requires exact matches.
    # Let's assume for now we validate strictly if we had the lists.
    # Since they are not fully provided in spec, we will skip strict value check for country/society 
    # unless we add a comprehensive list. 
    # We will implement the check: if key is in DROPDOWN_OPTIONS, we check it.
}

def validate_field_updates(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates a list of field updates against the schema.
    """
    valid_updates = []
    
    for update in updates:
        field_id = update.get("field_id")
        value = update.get("value")
        
        # Check field exists
        if field_id not in VALID_FIELD_IDS:
            continue
        
        # Type validation
        field_type = FIELD_TYPES.get(field_id)
        
        if field_type == "boolean":
            if not isinstance(value, bool):
                continue
        
        elif field_type == "number":
            if not isinstance(value, (int, float)):
                continue
        
        elif field_type == "dropdown":
            # Only validate against options if we have them defined
            if field_id in DROPDOWN_OPTIONS:
                if value not in DROPDOWN_OPTIONS[field_id]:
                    continue
        
        elif field_type == "date":
            # Validate ISO format YYYY-MM-DD
            if not isinstance(value, str):
                continue
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                continue
        
        elif field_type == "text":
             if not isinstance(value, str):
                continue

        valid_updates.append(update)
    
    return valid_updates
