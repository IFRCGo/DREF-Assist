# DREF Quality Evaluation Module

A standalone Django app for evaluating DREF (Disaster Response Emergency Fund) applications against IFRC quality control criteria.

## Overview

This module implements automated quality assessment that evaluates DREF applications against the IFRC rubric criteria, providing actionable improvement suggestions through integration with the existing chat interface.

### Two Modes of Operation

1. **Standalone Mode**: Use the REST API endpoints directly for DREF evaluation
2. **Integrated Mode**: Hook into the existing DREF serializers for real-time evaluation during form save

### Features

- **Two-Pass Evaluation System**
  - Pass 1: Rubric scoring against IFRC quality control criteria
  - Pass 2: Comparative analysis with reference examples (only if issues found)

- **Section-Level Evaluation**
  - Operation Overview
  - Event Detail
  - Actions & Needs
  - Operation
  - Operational Timeframe & Contacts

- **Accept/Don't Accept Outcomes** (No numeric scoring)

- **Improvement Suggestions** with ready-to-use prompts for the chat endpoint

- **Reference Database** for high-quality example applications

- **Evaluation History Tracking**

## Installation

### 1. Add to INSTALLED_APPS

In your Django settings (`main/settings.py`):

```python
INSTALLED_APPS = [
    # ... other apps
    'dref_evaluation',
]
```

### 2. Add URL Routes

In your main URL configuration (`main/urls.py`):

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('api/dref-evaluation/', include('dref_evaluation.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py migrate dref_evaluation
```

## API Endpoints

### Main Evaluation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dref-evaluation/evaluate/` | POST | Full DREF evaluation |
| `/api/dref-evaluation/evaluate/section/` | POST | Section-level evaluation |
| `/api/dref-evaluation/evaluate/auto-improve/` | POST | Auto-improve via chat |
| `/api/dref-evaluation/evaluate/rubric/` | GET | Get evaluation rubric |

### Evaluation Records

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dref-evaluation/evaluations/` | GET/POST | List/Create evaluations |
| `/api/dref-evaluation/evaluations/{id}/` | GET/PUT/DELETE | Manage evaluation |
| `/api/dref-evaluation/evaluations/by_dref/` | GET | Get by DREF ID |
| `/api/dref-evaluation/evaluations/latest_by_dref/` | GET | Get latest for DREF |

### Reference Examples

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dref-evaluation/reference-examples/` | GET/POST | List/Create references |
| `/api/dref-evaluation/reference-examples/search/` | GET | Search similar references |

## Usage

### Evaluate a DREF Form

```python
import requests

response = requests.post('/api/dref-evaluation/evaluate/', json={
    'dref_id': 123,
    'form_state': {
        'targeted_areas': 'Districts A, B, C',
        'event_description': 'Flooding affected...',
        # ... other fields
    }
})

result = response.json()
# {
#     'overall_status': 'accepted' | 'needs_revision',
#     'section_results': {...},
#     'improvement_suggestions': [...]
# }
```

### Evaluate a Specific Section

```python
response = requests.post('/api/dref-evaluation/evaluate/section/', json={
    'section_name': 'operation_overview',
    'form_state': {...}
})
```

### Auto-Improve

```python
response = requests.post('/api/dref-evaluation/evaluate/auto-improve/', json={
    'dref_id': 123,
    'form_state': {...},
    'max_improvements': 5
})
```

## Rubric Structure

The evaluation rubric is organized by form sections with criteria from the IFRC Quality Control checklist:

- **Operation Overview**: Targeted areas, crisis classification, map, lessons learnt
- **Event Detail**: Event description, trigger date, scope/scale, photos
- **Actions & Needs**: Coordination, NS activities, needs analysis, data sources
- **Operation**: Rationale, targeting, capacity, activities, security
- **Operational Timeframe & Contacts**: Budget, insurance, admin costs

Each criterion has:
- `required`: Whether it must pass for acceptance
- `criterion`: The quality control requirement
- `guidance`: Help text for improvement
- `condition`: Optional condition for applicability

## Backend Integration (Existing DREF System)

### Option 1: Evaluate on Save (in DrefSerializer)

Add evaluation feedback when a DREF is saved:

```python
# In dref/serializers.py
from dref_evaluation.integration import evaluate_dref_on_save, add_evaluation_to_response

class DrefSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    # ... existing code ...
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add evaluation summary to response
        data = add_evaluation_to_response(data, instance)
        return data
```

### Option 2: Evaluate Before Finalize

Add validation before DREF can be finalized:

```python
# In dref/views.py
from dref_evaluation.integration import evaluate_dref_on_save

class DrefViewSet(RevisionMixin, viewsets.ModelViewSet):
    @action(detail=True, url_path="finalize", methods=["post"])
    def finalize(self, request, pk=None, version=None):
        dref = self.get_object()
        
        # Evaluate before allowing finalization
        evaluation = evaluate_dref_on_save(dref)
        if evaluation['overall_status'] == 'needs_revision':
            return Response({
                'error': 'DREF needs revision before finalization',
                'evaluation': evaluation
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ... existing finalization code ...
```

### Option 3: Section-Level Validation (Real-Time)

Evaluate as users fill in each section:

```python
from dref_evaluation.integration import evaluate_section_data

# Frontend calls this when user completes a section
def validate_section(section_name, form_data):
    result = evaluate_section_data(section_name, form_data)
    return result
    # Returns: {'status': 'accept', 'issues': [], 'criteria_results': {...}}
```

### Option 4: Direct Form Data Evaluation

Evaluate serializer data without saving:

```python
from dref_evaluation.integration import evaluate_form_data

# In DrefSerializer.validate()
def validate(self, data):
    # ... existing validation ...
    
    # Run quality evaluation
    evaluation = evaluate_form_data(data)
    if evaluation['overall_status'] == 'needs_revision':
        # Add warnings (non-blocking)
        self.context['evaluation_warnings'] = evaluation['improvement_suggestions']
    
    return data
```

## Frontend Integration

Add an "Evaluate" button at the bottom of each DREF form section:

```jsx
<button onClick={() => evaluateSection('operation_overview')}>
  Evaluate Section
</button>
```

Display results with Accept/Don't Accept indicators and improvement suggestions:

```jsx
{result.criteria_results.map(criterion => (
  <div className={criterion.outcome === 'accept' ? 'success' : 'warning'}>
    {criterion.criterion}
    {criterion.outcome === 'dont_accept' && (
      <button onClick={() => applyImprovement(criterion.improvement_prompt)}>
        Apply Suggestion
      </button>
    )}
  </div>
))}
```

## Development

### Running Tests

```bash
pytest dref_evaluation/tests.py -v
```

### Project Structure

```
dref_evaluation/
Ôö£ÔöÇÔöÇ __init__.py
Ôö£ÔöÇÔöÇ apps.py
Ôö£ÔöÇÔöÇ models.py           # Database models
Ôö£ÔöÇÔöÇ evaluator.py        # Core evaluation logic
Ôö£ÔöÇÔöÇ integration.py      # Backend integration helpers
Ôö£ÔöÇÔöÇ serializers.py      # DRF serializers
Ôö£ÔöÇÔöÇ views.py            # API views
Ôö£ÔöÇÔöÇ urls.py             # URL routing
Ôö£ÔöÇÔöÇ admin.py            # Django admin
Ôö£ÔöÇÔöÇ tests.py            # Test suite
Ôö£ÔöÇÔöÇ evaluation_rubric.json  # IFRC quality criteria
Ôö£ÔöÇÔöÇ pyproject.toml      # Package config
Ôö£ÔöÇÔöÇ README.md           # This file
ÔööÔöÇÔöÇ migrations/
    Ôö£ÔöÇÔöÇ __init__.py
    ÔööÔöÇÔöÇ 0001_initial.py
```

## Integration Quick Reference

| Function | Use Case |
|----------|----------|
| `evaluate_dref_on_save(dref)` | Evaluate a saved Dref instance |
| `evaluate_form_data(data)` | Evaluate raw form data before save |
| `evaluate_section_data(section, data)` | Real-time section validation |
| `add_evaluation_to_response(data, dref)` | Add eval summary to serializer response |
| `get_section_guidance(section)` | Show criteria before user fills section |
| `dref_instance_to_form_state(dref)` | Convert Dref model to evaluation format |

## License

MIT License - See LICENSE file for details.
