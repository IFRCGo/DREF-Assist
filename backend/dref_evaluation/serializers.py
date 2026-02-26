from rest_framework import serializers
from .models import DrefEvaluation, DrefReferenceExample, EvaluationHistory


class CriterionResultSerializer(serializers.Serializer):
    """Serializer for individual criterion evaluation results."""
    criterion_id = serializers.CharField()
    field = serializers.CharField()
    criterion = serializers.CharField()
    outcome = serializers.ChoiceField(choices=['accept', 'dont_accept'])
    required = serializers.BooleanField()
    reasoning = serializers.CharField(allow_blank=True)
    improvement_prompt = serializers.CharField(allow_blank=True)
    guidance = serializers.CharField(allow_blank=True)


class SectionResultSerializer(serializers.Serializer):
    """Serializer for section evaluation results."""
    section_name = serializers.CharField()
    section_display_name = serializers.CharField()
    status = serializers.ChoiceField(choices=['accept', 'needs_revision'])
    criteria_results = serializers.DictField(child=CriterionResultSerializer())
    issues = serializers.ListField(child=serializers.CharField())


class ImprovementSuggestionSerializer(serializers.Serializer):
    """Serializer for improvement suggestions."""
    section = serializers.CharField()
    field = serializers.CharField()
    criterion = serializers.CharField()
    priority = serializers.IntegerField()
    guidance = serializers.CharField()
    ready_prompt = serializers.CharField()
    auto_applicable = serializers.BooleanField()


class EvaluationRequestSerializer(serializers.Serializer):
    """Serializer for evaluation requests."""
    dref_id = serializers.IntegerField(required=False)
    form_state = serializers.JSONField(required=True)
    section = serializers.CharField(required=False, allow_blank=True)


class EvaluationResponseSerializer(serializers.Serializer):
    """Serializer for evaluation responses."""
    dref_id = serializers.IntegerField()
    overall_status = serializers.ChoiceField(choices=['accepted', 'needs_revision', 'pending'])
    section_results = serializers.DictField(child=SectionResultSerializer())
    improvement_suggestions = ImprovementSuggestionSerializer(many=True)
    pass_one_completed = serializers.BooleanField()
    pass_two_completed = serializers.BooleanField()
    reference_examples_used = serializers.ListField(child=serializers.IntegerField())


class AutoImproveRequestSerializer(serializers.Serializer):
    """Serializer for auto-improve requests."""
    dref_id = serializers.IntegerField(required=False)
    form_state = serializers.JSONField(required=True)
    max_improvements = serializers.IntegerField(default=5, min_value=1, max_value=20)


class AutoImproveResponseSerializer(serializers.Serializer):
    """Serializer for auto-improve responses."""
    original_status = serializers.CharField()
    new_status = serializers.CharField()
    applied_improvements = serializers.ListField(
        child=serializers.DictField()
    )
    updated_form_state = serializers.JSONField()
    new_evaluation = EvaluationResponseSerializer()


class DrefEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for DrefEvaluation model."""
    
    class Meta:
        model = DrefEvaluation
        fields = [
            'id',
            'dref_id',
            'status',
            'section_results',
            'improvement_suggestions',
            'reference_examples_used',
            'evaluated_by',
            'created_at',
            'updated_at',
            'pass_one_completed',
            'pass_two_completed',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DrefEvaluationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing evaluations."""
    
    class Meta:
        model = DrefEvaluation
        fields = [
            'id',
            'dref_id',
            'status',
            'evaluated_by',
            'created_at',
            'pass_one_completed',
            'pass_two_completed',
        ]


class DrefReferenceExampleSerializer(serializers.ModelSerializer):
    """Serializer for DrefReferenceExample model."""
    
    class Meta:
        model = DrefReferenceExample
        fields = [
            'id',
            'title',
            'content',
            'disaster_type',
            'region',
            'operation_type',
            'quality_score',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DrefReferenceExampleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reference examples."""
    
    class Meta:
        model = DrefReferenceExample
        fields = [
            'id',
            'title',
            'disaster_type',
            'region',
            'operation_type',
            'quality_score',
            'is_active',
        ]


class EvaluationHistorySerializer(serializers.ModelSerializer):
    """Serializer for EvaluationHistory model."""
    
    class Meta:
        model = EvaluationHistory
        fields = [
            'id',
            'dref_id',
            'evaluation',
            'status_snapshot',
            'accepted_count',
            'total_count',
            'trigger',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SectionEvaluationRequestSerializer(serializers.Serializer):
    """Serializer for section-level evaluation requests."""
    section_name = serializers.ChoiceField(
        choices=[
            'operation_overview',
            'event_detail',
            'actions_needs',
            'operation',
            'operational_timeframe_contacts',
        ]
    )
    form_state = serializers.JSONField(required=True)
    dref_id = serializers.IntegerField(required=False)


class SectionEvaluationResponseSerializer(serializers.Serializer):
    """Serializer for section-level evaluation responses."""
    section_name = serializers.CharField()
    section_display_name = serializers.CharField()
    status = serializers.ChoiceField(choices=['accept', 'needs_revision'])
    criteria_results = serializers.DictField(child=CriterionResultSerializer())
    issues = serializers.ListField(child=serializers.CharField())
    improvement_suggestions = ImprovementSuggestionSerializer(many=True)


class RubricSerializer(serializers.Serializer):
    """Serializer for the evaluation rubric."""
    version = serializers.CharField()
    description = serializers.CharField()
    sections = serializers.DictField()
    evaluation_outcomes = serializers.DictField()

