from django.db import models


class DrefEvaluation(models.Model):
    """
    Stores evaluation results for a DREF application.
    Each evaluation contains results per section and overall status.
    """
    
    class EvaluationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        NEEDS_REVISION = 'needs_revision', 'Needs Revision'
    
    # Reference to the DREF being evaluated (store ID, don't create FK to avoid modifying existing models)
    dref_id = models.IntegerField(
        help_text="ID of the DREF application being evaluated"
    )
    
    # Overall evaluation status
    status = models.CharField(
        max_length=20,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING
    )
    
    # Section-level results stored as JSON
    section_results = models.JSONField(
        default=dict,
        help_text="Evaluation results for each section"
    )
    
    # Improvement suggestions
    improvement_suggestions = models.JSONField(
        default=list,
        help_text="List of improvement suggestions with ready-to-use prompts"
    )
    
    # Reference examples used in Pass 2 (if any)
    reference_examples_used = models.JSONField(
        default=list,
        help_text="IDs of reference examples used for comparative analysis"
    )
    
    # Evaluator (can be 'auto' for automated evaluation)
    evaluated_by = models.CharField(
        max_length=255,
        default='auto'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Pass tracking
    pass_one_completed = models.BooleanField(default=False)
    pass_two_completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "DREF Evaluation"
        verbose_name_plural = "DREF Evaluations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Evaluation for DREF #{self.dref_id} - {self.status}"
    
    def get_section_status(self, section_name):
        """Get the evaluation status for a specific section."""
        return self.section_results.get(section_name, {}).get('status', 'pending')
    
    def get_section_issues(self, section_name):
        """Get the list of issues for a specific section."""
        return self.section_results.get(section_name, {}).get('issues', [])
    
    def get_accepted_criteria_count(self, section_name=None):
        """Count accepted criteria, optionally for a specific section."""
        count = 0
        sections = [section_name] if section_name else self.section_results.keys()
        
        for section in sections:
            section_data = self.section_results.get(section, {})
            criteria_results = section_data.get('criteria_results', {})
            for criterion_id, result in criteria_results.items():
                if result.get('outcome') == 'accept':
                    count += 1
        return count
    
    def calculate_overall_status(self):
        """Calculate and set the overall evaluation status based on section results."""
        has_dont_accept = False
        
        for section_name, section_data in self.section_results.items():
            criteria_results = section_data.get('criteria_results', {})
            for criterion_id, result in criteria_results.items():
                if result.get('required', False) and result.get('outcome') == 'dont_accept':
                    has_dont_accept = True
                    break
            if has_dont_accept:
                break
        
        self.status = self.EvaluationStatus.NEEDS_REVISION if has_dont_accept else self.EvaluationStatus.ACCEPTED
        return self.status


class DrefReferenceExample(models.Model):
    """
    High-scoring example applications used for comparative analysis in Pass 2.
    These serve as reference for generating improvement suggestions.
    """
    
    # Title/identifier for the reference
    title = models.CharField(max_length=255)
    
    # The actual DREF content (anonymized/sanitized)
    content = models.JSONField(
        help_text="The reference DREF form content organized by sections"
    )
    
    # Embedding vector for similarity search (stored as JSON array of floats)
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vector embedding for similarity-based retrieval"
    )
    
    # Metadata
    disaster_type = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    operation_type = models.CharField(max_length=100, blank=True)
    
    # Quality indicators
    quality_score = models.FloatField(
        default=0.0,
        help_text="Quality score (0-100) of this reference example"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Active flag
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "DREF Reference Example"
        verbose_name_plural = "DREF Reference Examples"
        ordering = ['-quality_score']
    
    def __str__(self):
        return f"{self.title} (Score: {self.quality_score})"


class EvaluationHistory(models.Model):
    """
    Tracks evaluation history for a DREF to show improvement over time.
    """
    
    dref_id = models.IntegerField()
    evaluation = models.ForeignKey(
        DrefEvaluation,
        on_delete=models.CASCADE,
        related_name='history_entries'
    )
    
    # Snapshot of status at this point
    status_snapshot = models.CharField(max_length=20)
    accepted_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    
    # What triggered this history entry
    trigger = models.CharField(
        max_length=50,
        choices=[
            ('initial', 'Initial Evaluation'),
            ('re_evaluation', 'Re-evaluation'),
            ('auto_improve', 'Auto Improvement Applied'),
            ('manual_edit', 'Manual Edit'),
        ]
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Evaluation History"
        verbose_name_plural = "Evaluation Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"History for DREF #{self.dref_id} at {self.created_at}"

