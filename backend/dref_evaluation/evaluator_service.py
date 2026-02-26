"""
Simple Azure OpenAI-powered DREF Evaluator Service
Provides clean evaluation of DREF applications using GPT-4o
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Dict, Any, List, Optional

# Load environment variables from .env file in backend directory
backend_dir = Path(__file__).resolve().parent.parent
env_file = backend_dir / '.env'
print(f"Loading .env from: {env_file}")
load_dotenv(env_file)


class DREFEvaluatorService:
    """Evaluates DREF applications using Azure OpenAI GPT-4o"""
    
    def __init__(self):
        """Initialize the evaluator with Azure OpenAI client"""
        print("Initializing DREFEvaluatorService...")
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.rubric = self._load_rubric()
        print(f"Rubric sections loaded: {list(self.rubric.get('sections', {}).keys())}")
        print(f"Full rubric: {self.rubric}")
    
    def _load_rubric(self) -> Dict[str, Any]:
        """Load the evaluation rubric"""
        try:
            rubric_path = os.path.join(os.path.dirname(__file__), 'evaluation_rubric.json')
            with open(rubric_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rubric: {e}")
            return {}
    
    def evaluate_dref(self, form_data: Dict[str, Any], section: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate a DREF application or specific section
        
        Args:
            form_data: The DREF form data to evaluate
            section: Optional specific section to evaluate
        
        Returns:
            Dictionary with evaluation results including status, issues, and suggestions
        """
        
        # Map section names to rubric sections
        section_mapping = {
            "essential_information": "operation_overview",
            "event_detail": "event_detail",
            "actions_needs": "actions_needs",
            "operation": "operation",
            "timeframes_contacts": "operational_timeframe_contacts"
        }
        
        rubric_section = section_mapping.get(section, section)
        
        # Get criteria for this section
        if rubric_section not in self.rubric.get('sections', {}):
            return {
                "status": "error",
                "message": f"Section {section} not found in rubric"
            }
        
        section_criteria = self.rubric['sections'][rubric_section]['criteria']
        
        # Create evaluation prompt with rubric criteria
        prompt = self._create_rubric_based_prompt(form_data, section_criteria, rubric_section)
        
        try:
            print(f"Calling Azure OpenAI with deployment: {self.deployment}")
            print(f"API Key set: {bool(os.getenv('AZURE_OPENAI_API_KEY'))}")
            print(f"API Key length: {len(os.getenv('AZURE_OPENAI_API_KEY') or '')}")
            print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert DREF evaluator. Evaluate the provided form fields against the rubric criteria. Return JSON with: status (approved/needs_revision), issues (array of {field, criterion, issue}), strengths (array of strings), and assessment (text summary)."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            print(f"Azure API response received successfully")
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Look for JSON in code blocks or plain text
                if '```json' in response_text:
                    json_str = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    json_str = response_text.split('```')[1].split('```')[0]
                else:
                    json_str = response_text
                
                evaluation = json.loads(json_str)
            except Exception as parse_error:
                print(f"JSON parse error: {parse_error}")
                # Fallback if JSON parsing fails
                evaluation = {
                    "status": "needs_revision" if "issue" in response_text.lower() else "approved",
                    "assessment": response_text,
                    "issues": [],
                    "strengths": []
                }
            
            return {
                "status": "success",
                "evaluation": evaluation,
                "raw_response": response_text
            }
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"Evaluation error ({error_type}): {error_msg}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": error_msg,
                "error_type": error_type
            }
    
    def _create_rubric_based_prompt(self, form_data: Dict[str, Any], criteria: List[Dict], section: str) -> str:
        """Create evaluation prompt based on rubric criteria"""
        
        prompt = f"""Evaluate the following DREF form section against the rubric criteria.

SECTION: {section}

FORM DATA:
{json.dumps(form_data, indent=2)}

RUBRIC CRITERIA TO CHECK:
"""
        
        for c in criteria:
            prompt += f"""
- Field: {c.get('field', 'N/A')}
  Criterion: {c.get('criterion', 'N/A')}
  Required: {c.get('required', False)}
  Guidance: {c.get('guidance', 'N/A')}
"""
        
        prompt += """

EVALUATION INSTRUCTIONS:
1. Check if each required field is present and contains substantial information
2. Assess if the content meets the criterion described
3. Return a JSON response with this structure:
{
  "status": "approved" or "needs_revision",
  "assessment": "Brief overall assessment",
  "issues": [
    {"field": "field_name", "criterion": "criterion_text", "issue": "specific problem"}
  ],
  "strengths": [
    "What was done well"
  ]
}

Provide honest feedback. Focus on substantive completeness, clarity, and alignment with IFRC standards."""
        
        return prompt
    
    def get_improvement_suggestions(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI-powered improvement suggestions for DREF application
        
        Args:
            form_data: The DREF form data
        
        Returns:
            Dictionary with improvement suggestions
        """
        try:
            prompt = f"""Based on this DREF application data, provide specific, actionable improvement suggestions:

{json.dumps(form_data, indent=2)}

Provide suggestions as a numbered list focusing on:
1. Missing or incomplete information
2. Unclear explanations that need clarification
3. Inconsistencies across sections
4. Areas that don't meet IFRC quality standards
5. Ways to strengthen the application"""
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert DREF quality improvement consultant. Provide constructive, specific suggestions to improve DREF applications."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "status": "success",
                "suggestions": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# Singleton instance
_evaluator_instance = None


def get_evaluator() -> DREFEvaluatorService:
    """Get or create the singleton evaluator instance"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = DREFEvaluatorService()
    return _evaluator_instance

