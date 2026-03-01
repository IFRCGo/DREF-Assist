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

    # actions_needs
    "actions_needs.ns_actions_started",
    "actions_needs.ns_action_types",
    "actions_needs.ifrc_description",
    "actions_needs.participating_ns",
    "actions_needs.icrc_description",
    "actions_needs.gov_requested_assistance",
    "actions_needs.national_authorities_actions",
    "actions_needs.un_other_actors",
    "actions_needs.coordination_mechanisms",
    "actions_needs.identified_gaps",

    # operation
    "operation.overall_objective",
    "operation.strategy_rationale",
    "operation.targeting_description",
    "operation.selection_criteria",
    "operation.targeted_women",
    "operation.targeted_men",
    "operation.targeted_girls",
    "operation.targeted_boys",
    "operation.targeted_total",
    "operation.people_with_disability",
    "operation.urban_population",
    "operation.rural_population",
    "operation.people_on_the_move",
    "operation.has_anti_fraud_policy",
    "operation.has_psea_policy",
    "operation.has_child_protection_policy",
    "operation.has_whistleblower_policy",
    "operation.has_anti_harassment_policy",
    "operation.risk_analysis",
    "operation.security_concerns",
    "operation.child_safeguarding_assessment",
    "operation.requested_amount_chf",
    "operation.staff_volunteers",
    "operation.volunteer_diversity",
    "operation.surge_personnel",
    "operation.procurement",
    "operation.monitoring",
    "operation.communication_strategy",

    # timeframes_contacts
    "timeframes_contacts.ns_application_date",
    "timeframes_contacts.operation_timeframe_months",
    "timeframes_contacts.appeal_code",
    "timeframes_contacts.glide_number",
    "timeframes_contacts.ns_contact_name",
    "timeframes_contacts.ns_contact_title",
    "timeframes_contacts.ns_contact_email",
    "timeframes_contacts.ns_contact_phone",
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

    # actions_needs
    "actions_needs.ns_actions_started": "boolean",
    "actions_needs.ns_action_types": "multi_select",
    "actions_needs.ifrc_description": "text",
    "actions_needs.participating_ns": "text",
    "actions_needs.icrc_description": "text",
    "actions_needs.gov_requested_assistance": "boolean",
    "actions_needs.national_authorities_actions": "text",
    "actions_needs.un_other_actors": "text",
    "actions_needs.coordination_mechanisms": "boolean",
    "actions_needs.identified_gaps": "text",

    # operation
    "operation.overall_objective": "text",
    "operation.strategy_rationale": "text",
    "operation.targeting_description": "text",
    "operation.selection_criteria": "text",
    "operation.targeted_women": "number",
    "operation.targeted_men": "number",
    "operation.targeted_girls": "number",
    "operation.targeted_boys": "number",
    "operation.targeted_total": "number",
    "operation.people_with_disability": "number",
    "operation.urban_population": "number",
    "operation.rural_population": "number",
    "operation.people_on_the_move": "number",
    "operation.has_anti_fraud_policy": "boolean",
    "operation.has_psea_policy": "boolean",
    "operation.has_child_protection_policy": "boolean",
    "operation.has_whistleblower_policy": "boolean",
    "operation.has_anti_harassment_policy": "boolean",
    "operation.risk_analysis": "text",
    "operation.security_concerns": "text",
    "operation.child_safeguarding_assessment": "boolean",
    "operation.requested_amount_chf": "number",
    "operation.staff_volunteers": "text",
    "operation.volunteer_diversity": "text",
    "operation.surge_personnel": "boolean",
    "operation.procurement": "text",
    "operation.monitoring": "text",
    "operation.communication_strategy": "text",

    # timeframes_contacts
    "timeframes_contacts.ns_application_date": "date",
    "timeframes_contacts.operation_timeframe_months": "number",
    "timeframes_contacts.appeal_code": "text",
    "timeframes_contacts.glide_number": "text",
    "timeframes_contacts.ns_contact_name": "text",
    "timeframes_contacts.ns_contact_title": "text",
    "timeframes_contacts.ns_contact_email": "text",
    "timeframes_contacts.ns_contact_phone": "text",
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
    "actions_needs.ns_action_types": [
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
        "Other",
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

FIELD_METADATA = {
    # --- operation_overview ---
    "operation_overview.national_society": {
        "category": "factual",
        "description": "The name of the National Red Cross/Red Crescent Society leading the operation.",
        "extraction_hint": "Look for explicit mentions of a National Society (e.g., 'Bangladesh Red Crescent Society'). Only populate if a specific society is named.",
    },
    "operation_overview.dref_type": {
        "category": "inferred",
        "description": "The type of DREF allocation: Imminent Crisis (before disaster strikes), Response (after disaster), or Protracted Crisis (ongoing long-term).",
        "extraction_hint": "Infer from the event description. If the disaster has already occurred, use 'Response'. If it is forecasted or imminent, use 'Imminent Crisis'. If it describes an ongoing, long-term crisis, use 'Protracted Crisis'.",
    },
    "operation_overview.disaster_type": {
        "category": "factual",
        "description": "The primary type of disaster from the allowed list.",
        "extraction_hint": "Match the described event to the closest dropdown option. Map synonyms: 'tropical storm'/'hurricane'/'typhoon' to 'Cyclone'; 'cholera outbreak'/'disease' to 'Epidemic'; 'mudslide' to 'Landslide'.",
    },
    "operation_overview.disaster_onset": {
        "category": "inferred",
        "description": "Whether the disaster was sudden or slow-onset.",
        "extraction_hint": "Infer from the nature of the event. Earthquakes, cyclones, floods from storms, tsunamis, volcanic eruptions are 'Sudden'. Droughts, epidemics growing over weeks/months, slow-moving population displacement are 'Slow'.",
    },
    "operation_overview.disaster_category": {
        "category": "inferred",
        "description": "IFRC disaster severity category: Yellow (limited impact), Orange (moderate impact), Red (severe/large-scale impact).",
        "extraction_hint": "Infer from scale and impact. Yellow: localized, limited casualties, community can mostly cope. Orange: significant damage, hundreds to thousands affected. Red: widespread devastation, thousands+ affected, exceeds local capacity. Consider affected population size, geographic spread, and severity described.",
    },
    "operation_overview.country": {
        "category": "factual",
        "description": "The country where the disaster occurred.",
        "extraction_hint": "Look for explicit country mentions. May appear in location descriptions, datelines, or organizational references (e.g., 'Bangladesh Red Crescent' implies Bangladesh).",
    },
    "operation_overview.region_province": {
        "category": "factual",
        "description": "The specific region, province, or state affected within the country.",
        "extraction_hint": "Look for sub-national geographic references: provinces, states, districts, regions, departments. Multiple regions can be listed separated by commas.",
    },
    "operation_overview.dref_title": {
        "category": "synthesized",
        "description": "A concise title for the DREF operation, typically formatted as 'Country: Disaster Type' or 'Country: Brief Description'.",
        "extraction_hint": "Compose from the country and disaster type once both are known. Examples: 'Bangladesh: Flood', 'Nepal: Earthquake', 'Mozambique: Cyclone Freddy'. Only compose if sufficient information is available.",
    },
    "operation_overview.emergency_appeal_planned": {
        "category": "inferred",
        "description": "Whether an Emergency Appeal is planned to follow this DREF allocation.",
        "extraction_hint": "Look for explicit statements about emergency appeal plans. Can also infer: if the disaster is Red category or very large-scale, an emergency appeal is likely planned (true). If not mentioned and scale is small, default to not setting this field.",
    },
    # --- event_detail ---
    "event_detail.date_trigger_met": {
        "category": "factual",
        "description": "The date when the DREF trigger criteria were met, in ISO format YYYY-MM-DD.",
        "extraction_hint": "Look for the date the disaster occurred or was declared. Must be an explicit date, not relative terms like 'last week'. Convert named dates (e.g., 'January 15, 2024') to ISO format.",
    },
    "event_detail.total_affected_population": {
        "category": "factual",
        "description": "The total number of people affected by the disaster.",
        "extraction_hint": "Only populate if an explicit total number is stated. Look for phrases like 'X people affected', 'X families affected' (multiply by household size only if the report itself provides the multiplier). Do NOT guess or round.",
    },
    "event_detail.people_in_need": {
        "category": "factual",
        "description": "The number of people in need of assistance (may be less than total affected).",
        "extraction_hint": "Look for explicit statements about people needing assistance, humanitarian aid, or emergency support. This is often a subset of total affected. Only populate if distinctly stated.",
    },
    "event_detail.estimated_male_affected": {
        "category": "factual",
        "description": "The estimated number of males affected.",
        "extraction_hint": "Only populate if the source explicitly provides a gender breakdown. Never calculate or assume from total affected population.",
    },
    "event_detail.estimated_female_affected": {
        "category": "factual",
        "description": "The estimated number of females affected.",
        "extraction_hint": "Only populate if the source explicitly provides a gender breakdown. Never calculate or assume from total affected population.",
    },
    "event_detail.estimated_girls_under_18": {
        "category": "factual",
        "description": "The estimated number of girls under 18 affected.",
        "extraction_hint": "Only populate if the source explicitly provides an age and gender breakdown for children. Never calculate or assume.",
    },
    "event_detail.estimated_boys_under_18": {
        "category": "factual",
        "description": "The estimated number of boys under 18 affected.",
        "extraction_hint": "Only populate if the source explicitly provides an age and gender breakdown for children. Never calculate or assume.",
    },
    "event_detail.what_happened": {
        "category": "synthesized",
        "description": "A narrative summary of the disaster event: what occurred, when, where, the immediate impact, and the current situation.",
        "extraction_hint": "Synthesize from ALL available source material into a coherent narrative paragraph. Combine scattered facts (event description, timeline, geographic scope, impact statistics, current conditions) into a comprehensive summary. Do not copy verbatim from sources; compose in your own words while preserving all factual details. This field SHOULD be populated whenever event information is available, even if it requires combining details from multiple sections of a document.",
    },
    # --- actions_needs ---
    "actions_needs.ns_actions_started": {
        "category": "inferred",
        "description": "Whether the National Society has started any response actions.",
        "extraction_hint": "Infer from mentions of National Society activities such as deploying volunteers, distributing relief items, conducting assessments, or activating contingency plans. If any NS response activity is described, set to true.",
    },
    "actions_needs.ns_action_types": {
        "category": "inferred",
        "description": "The types of response actions the National Society has started or is carrying out. Multi-select from allowed options.",
        "extraction_hint": "Infer from descriptions of NS activities. Map activities to the closest option(s): relief distribution → 'Shelter, Housing And Settlements' or 'Multi Purpose Cash'; medical teams → 'Health'; water/sanitation → 'Water, Sanitation and Hygiene'; evacuations/search and rescue → 'Assessment'; volunteer mobilization → 'National Society Readiness'. Return as an array of matching option strings.",
    },
    "actions_needs.ifrc_description": {
        "category": "synthesized",
        "description": "Description of IFRC presence, support, and coordination role in the operation.",
        "extraction_hint": "Synthesize information about IFRC's involvement: surge deployments, technical support, coordination with NS, funding mechanisms, or regional office engagement. Combine details from multiple sources if available.",
    },
    "actions_needs.participating_ns": {
        "category": "synthesized",
        "description": "Description of Participating National Societies' contributions and presence.",
        "extraction_hint": "Synthesize information about other National Societies providing bilateral support, personnel, funding, or technical assistance. List specific societies and their contributions if mentioned.",
    },
    "actions_needs.icrc_description": {
        "category": "synthesized",
        "description": "Description of ICRC presence and activities in the affected area.",
        "extraction_hint": "Synthesize information about ICRC operations, protection activities, or coordination. Include details about ICRC programs, staff presence, or joint activities with the NS.",
    },
    "actions_needs.gov_requested_assistance": {
        "category": "factual",
        "description": "Whether the government has formally requested international assistance.",
        "extraction_hint": "Only populate if the source explicitly states that the government has (or has not) requested international assistance. Look for official declarations or formal requests.",
    },
    "actions_needs.national_authorities_actions": {
        "category": "synthesized",
        "description": "Actions taken by national and local government authorities in response to the disaster.",
        "extraction_hint": "Synthesize information about government response: evacuations, emergency declarations, military deployment, relief distribution, infrastructure repairs. Combine details from multiple sources.",
    },
    "actions_needs.un_other_actors": {
        "category": "synthesized",
        "description": "Actions by UN agencies and other humanitarian actors present in the affected area.",
        "extraction_hint": "Synthesize information about UN agencies (OCHA, UNICEF, WFP, etc.), NGOs, and other actors. Include their activities, coordination role, and contributions to the response.",
    },
    "actions_needs.coordination_mechanisms": {
        "category": "inferred",
        "description": "Whether major coordination mechanisms (clusters, working groups, EOCs) are in place.",
        "extraction_hint": "Infer from mentions of humanitarian clusters, coordination meetings, Emergency Operations Centers (EOCs), or inter-agency working groups. If coordination structures are described, set to true.",
    },
    "actions_needs.identified_gaps": {
        "category": "synthesized",
        "description": "Identified gaps or limitations in the needs assessment or response capacity.",
        "extraction_hint": "Synthesize information about assessment limitations, data gaps, access constraints, capacity shortfalls, or unmet needs. Include both assessment methodology gaps and response capability gaps.",
    },
    # --- operation ---
    "operation.overall_objective": {
        "category": "synthesized",
        "description": "The overall objective of the DREF operation, describing what it aims to achieve.",
        "extraction_hint": "Synthesize from the operation's goals, target population, and planned outcomes. Typically follows the format: 'This DREF operation aims to provide [type of assistance] to [number] [target group] affected by [disaster] in [location].'",
    },
    "operation.strategy_rationale": {
        "category": "synthesized",
        "description": "The rationale behind the operation strategy, explaining why this approach was chosen.",
        "extraction_hint": "Synthesize from needs assessment findings, NS capacity, geographic considerations, and intervention logic. Explain the connection between identified needs and planned response activities.",
    },
    "operation.targeting_description": {
        "category": "synthesized",
        "description": "Description of who will be targeted through this operation and why.",
        "extraction_hint": "Synthesize from vulnerability assessments, geographic targeting, and population profiles. Describe the target groups (e.g., displaced families, most vulnerable communities) and the rationale for targeting them.",
    },
    "operation.selection_criteria": {
        "category": "synthesized",
        "description": "The criteria used to select the targeted population for assistance.",
        "extraction_hint": "Synthesize from assessment data and operational planning. Include criteria such as vulnerability level, geographic location, displacement status, socioeconomic factors, or specific needs (elderly, disabled, female-headed households).",
    },
    "operation.targeted_women": {
        "category": "factual",
        "description": "The number of women targeted for assistance in this operation.",
        "extraction_hint": "Only populate if the source explicitly provides a gender breakdown of the targeted population. Never calculate or assume from the total targeted population.",
    },
    "operation.targeted_men": {
        "category": "factual",
        "description": "The number of men targeted for assistance in this operation.",
        "extraction_hint": "Only populate if the source explicitly provides a gender breakdown of the targeted population. Never calculate or assume from the total targeted population.",
    },
    "operation.targeted_girls": {
        "category": "factual",
        "description": "The number of girls (under 18) targeted for assistance.",
        "extraction_hint": "Only populate if the source explicitly provides an age and gender breakdown for children in the targeted population. Never calculate or assume.",
    },
    "operation.targeted_boys": {
        "category": "factual",
        "description": "The number of boys (under 18) targeted for assistance.",
        "extraction_hint": "Only populate if the source explicitly provides an age and gender breakdown for children in the targeted population. Never calculate or assume.",
    },
    "operation.targeted_total": {
        "category": "factual",
        "description": "The total number of people targeted for assistance in this operation.",
        "extraction_hint": "Only populate if an explicit total target number is stated. Look for phrases like 'targeting X people/families/households'. If stated in families, multiply only if the report provides the household size multiplier.",
    },
    "operation.people_with_disability": {
        "category": "factual",
        "description": "The estimated number of people with disabilities in the targeted population.",
        "extraction_hint": "Only populate if the source explicitly provides disability statistics for the targeted population. Never estimate based on general population percentages.",
    },
    "operation.urban_population": {
        "category": "factual",
        "description": "The number of targeted people in urban areas.",
        "extraction_hint": "Only populate if the source explicitly provides an urban/rural breakdown of the targeted population.",
    },
    "operation.rural_population": {
        "category": "factual",
        "description": "The number of targeted people in rural areas.",
        "extraction_hint": "Only populate if the source explicitly provides an urban/rural breakdown of the targeted population.",
    },
    "operation.people_on_the_move": {
        "category": "factual",
        "description": "The estimated number of people on the move (displaced, migrating) in the targeted area.",
        "extraction_hint": "Only populate if the source explicitly mentions displaced persons, refugees, or migrants with a specific number. Look for IDP figures, displacement statistics, or migration data.",
    },
    "operation.has_anti_fraud_policy": {
        "category": "factual",
        "description": "Whether the National Society has an anti-fraud and corruption policy.",
        "extraction_hint": "Only populate if the source explicitly states whether the NS has this policy. Typically found in institutional capacity assessments or NS self-assessments.",
    },
    "operation.has_psea_policy": {
        "category": "factual",
        "description": "Whether the National Society has a prevention of sexual exploitation and abuse (PSEA) policy.",
        "extraction_hint": "Only populate if the source explicitly states whether the NS has a PSEA policy. Typically found in institutional capacity assessments.",
    },
    "operation.has_child_protection_policy": {
        "category": "factual",
        "description": "Whether the National Society has a child protection/child safeguarding policy.",
        "extraction_hint": "Only populate if the source explicitly states whether the NS has a child protection policy. Typically found in institutional assessments or safeguarding documentation.",
    },
    "operation.has_whistleblower_policy": {
        "category": "factual",
        "description": "Whether the National Society has a whistleblower protection policy.",
        "extraction_hint": "Only populate if the source explicitly states whether the NS has a whistleblower policy. Typically found in institutional capacity assessments.",
    },
    "operation.has_anti_harassment_policy": {
        "category": "factual",
        "description": "Whether the National Society has an anti-sexual harassment policy.",
        "extraction_hint": "Only populate if the source explicitly states whether the NS has an anti-harassment policy. Typically found in institutional assessments or HR documentation.",
    },
    "operation.risk_analysis": {
        "category": "synthesized",
        "description": "Analysis of potential risks for this operation, their root causes, and mitigation actions.",
        "extraction_hint": "Synthesize from risk assessments, security analyses, and operational challenges. Include contextual risks (conflict, access), programmatic risks (supply chain, targeting), and institutional risks (capacity, compliance). Reference Annex III risk categories where applicable.",
    },
    "operation.security_concerns": {
        "category": "synthesized",
        "description": "Security and safety concerns for the operation.",
        "extraction_hint": "Synthesize from security assessments and context analysis. Include physical security risks, access constraints, conflict dynamics, and any safety protocols or measures planned for staff and volunteers.",
    },
    "operation.child_safeguarding_assessment": {
        "category": "factual",
        "description": "Whether the child safeguarding risk analysis assessment has been completed.",
        "extraction_hint": "Only populate if the source explicitly states whether a child safeguarding risk assessment has been completed for this operation.",
    },
    "operation.requested_amount_chf": {
        "category": "factual",
        "description": "The total amount requested for this DREF operation in Swiss Francs (CHF).",
        "extraction_hint": "Only populate if an explicit funding amount is stated in CHF. Look for budget totals, funding requests, or allocation amounts. Do not convert from other currencies unless the conversion is provided in the source.",
    },
    "operation.staff_volunteers": {
        "category": "synthesized",
        "description": "Description of staff and volunteers who will be involved in this operation.",
        "extraction_hint": "Synthesize from operational planning details. Include numbers and roles of staff, volunteers, and any specialized personnel. Mention training status and deployment plans if available.",
    },
    "operation.volunteer_diversity": {
        "category": "synthesized",
        "description": "Whether the volunteer team reflects the gender, age, and cultural diversity of the affected population.",
        "extraction_hint": "Synthesize from volunteer deployment plans and diversity data. Describe how the volunteer team composition relates to the demographics of the affected community.",
    },
    "operation.surge_personnel": {
        "category": "inferred",
        "description": "Whether surge personnel will be deployed for this operation.",
        "extraction_hint": "Infer from mentions of FACT teams, ERU deployments, RDRT/NDRT mobilization, or other surge capacity mechanisms. If surge support is mentioned or the scale of the disaster suggests it, set to true.",
    },
    "operation.procurement": {
        "category": "synthesized",
        "description": "Description of procurement arrangements — whether done by NS or IFRC.",
        "extraction_hint": "Synthesize from operational planning details about procurement responsibilities, supply chain arrangements, and pre-positioned stock usage. Note whether procurement will be handled by the NS, IFRC, or both.",
    },
    "operation.monitoring": {
        "category": "synthesized",
        "description": "Description of how the operation will be monitored.",
        "extraction_hint": "Synthesize from monitoring and evaluation plans. Include monitoring methods (field visits, surveys, community feedback), reporting frequency, and key indicators that will be tracked.",
    },
    "operation.communication_strategy": {
        "category": "synthesized",
        "description": "The National Society's communication strategy for this operation.",
        "extraction_hint": "Synthesize from communication plans. Include community engagement approaches, media strategy, social media plans, beneficiary communication and accountability (CBA) mechanisms, and key messages.",
    },
    # --- timeframes_contacts ---
    "timeframes_contacts.ns_application_date": {
        "category": "factual",
        "description": "The date when the National Society submitted its DREF application, in ISO format YYYY-MM-DD.",
        "extraction_hint": "Look for the date the NS submitted or prepared the DREF application. Must be an explicit date. Convert named dates to ISO format.",
    },
    "timeframes_contacts.operation_timeframe_months": {
        "category": "factual",
        "description": "The planned duration of the operation in months.",
        "extraction_hint": "Only populate if the source explicitly states the operation duration. Look for phrases like 'X-month operation' or 'implementation period of X months'.",
    },
    "timeframes_contacts.appeal_code": {
        "category": "factual",
        "description": "The IFRC appeal code for this operation (e.g., MDRBD028).",
        "extraction_hint": "Look for explicit appeal codes, typically formatted as MDR followed by country and number codes. Only populate if explicitly stated.",
    },
    "timeframes_contacts.glide_number": {
        "category": "factual",
        "description": "The GLIDE (GLobal IDEntifier) number for the disaster event.",
        "extraction_hint": "Look for GLIDE numbers, typically formatted as disaster-type abbreviation followed by date and country code (e.g., FL-2024-000001-BGD). Only populate if explicitly stated.",
    },
    "timeframes_contacts.ns_contact_name": {
        "category": "factual",
        "description": "The name of the National Society contact person for this operation.",
        "extraction_hint": "Look for named NS focal points, operation coordinators, or disaster management officers. Only populate if a specific person's name is provided.",
    },
    "timeframes_contacts.ns_contact_title": {
        "category": "factual",
        "description": "The job title of the National Society contact person.",
        "extraction_hint": "Look for the title or position associated with the NS contact person. Only populate if explicitly stated alongside the contact name.",
    },
    "timeframes_contacts.ns_contact_email": {
        "category": "factual",
        "description": "The email address of the National Society contact person.",
        "extraction_hint": "Look for email addresses associated with the NS contact person. Only populate if an explicit email address is provided.",
    },
    "timeframes_contacts.ns_contact_phone": {
        "category": "factual",
        "description": "The phone number of the National Society contact person.",
        "extraction_hint": "Look for phone numbers associated with the NS contact person. Only populate if an explicit phone number is provided.",
    },
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
        
        elif field_type == "multi_select":
            if not isinstance(value, list):
                continue
            # Validate each item against allowed options if defined
            if field_id in DROPDOWN_OPTIONS:
                allowed = DROPDOWN_OPTIONS[field_id]
                value = [v for v in value if v in allowed]
                if not value:
                    continue
                update = {**update, "value": value}

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
