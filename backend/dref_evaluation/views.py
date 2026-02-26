from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import DrefEvaluation, DrefReferenceExample, EvaluationHistory
from .serializers import (
    DrefEvaluationSerializer,
    DrefEvaluationListSerializer,
    DrefReferenceExampleSerializer,
    DrefReferenceExampleListSerializer,
    EvaluationHistorySerializer,
    EvaluationRequestSerializer,
    EvaluationResponseSerializer,
    AutoImproveRequestSerializer,
    AutoImproveResponseSerializer,
    SectionEvaluationRequestSerializer,
    SectionEvaluationResponseSerializer,
    RubricSerializer,
)
from .evaluator import DrefEvaluator, AutoImprover, RubricLoader
from .evaluator_service import get_evaluator


class AIEvaluateView(APIView):
    """
    POST /api/v2/dref-evaluation/ai-evaluate/
    
    AI-powered evaluation using Azure OpenAI GPT-4o.
    Evaluates a DREF form state and returns structured feedback.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Evaluate DREF application or specific section using AI.
        
        Request body:
        {
            "form_data": {form fields...},
            "section": "operation_overview" (optional)
        }
        """
        try:
            form_data = request.data.get('form_data', {})
            section = request.data.get('section')
            
            if not form_data:
                return Response(
                    {'error': 'form_data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get evaluator service
            evaluator = get_evaluator()
            
            # Perform evaluation
            result = evaluator.evaluate_dref(form_data, section)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AISuggestionsView(APIView):
    """
    POST /api/v2/dref-evaluation/ai-suggestions/
    
    Get AI-powered improvement suggestions for a DREF application.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Get improvement suggestions for DREF application.
        
        Request body:
        {
            "form_data": {form fields...}
        }
        """
        try:
            form_data = request.data.get('form_data', {})
            
            if not form_data:
                return Response(
                    {'error': 'form_data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get evaluator service
            evaluator = get_evaluator()
            
            # Get suggestions
            suggestions_result = evaluator.get_improvement_suggestions(form_data)
            
            # Extract suggestions text from result
            suggestions_text = suggestions_result.get('suggestions', suggestions_result.get('message', str(suggestions_result)))
            
            return Response(
                {'suggestions': suggestions_text},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EvaluateView(APIView):
    """
    POST /evaluate
    
    Evaluates a DREF form state against the IFRC rubric criteria.
    Returns overall status, criterion breakdown, and improvement suggestions.
    """
    permission_classes = [AllowAny]  # Adjust as needed
    
    def post(self, request):
        serializer = EvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        form_state = serializer.validated_data['form_state']
        dref_id = serializer.validated_data.get('dref_id', 0)
        section = serializer.validated_data.get('section')
        
        evaluator = DrefEvaluator()
        
        if section:
            # Section-level evaluation
            try:
                section_result = evaluator.evaluate_section(section, form_state, dref_id)
                
                # Generate improvement suggestions for this section
                suggestions = []
                for cid, cr in section_result.criteria_results.items():
                    if cr.outcome == 'dont_accept':
                        suggestions.append({
                            'section': section,
                            'field': cr.field,
                            'criterion': cr.criterion,
                            'priority': 1 if cr.required else 2,
                            'guidance': cr.guidance,
                            'ready_prompt': cr.improvement_prompt,
                            'auto_applicable': True
                        })
                
                response_data = {
                    'section_name': section_result.section_name,
                    'section_display_name': section_result.section_display_name,
                    'status': section_result.status,
                    'criteria_results': {
                        cid: {
                            'criterion_id': cr.criterion_id,
                            'field': cr.field,
                            'criterion': cr.criterion,
                            'outcome': cr.outcome,
                            'required': cr.required,
                            'reasoning': cr.reasoning,
                            'improvement_prompt': cr.improvement_prompt,
                            'guidance': cr.guidance,
                        }
                        for cid, cr in section_result.criteria_results.items()
                    },
                    'issues': section_result.issues,
                    'improvement_suggestions': suggestions
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
            
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Full evaluation
        evaluation_result = evaluator.evaluate(dref_id, form_state)
        response_data = evaluator.to_dict(evaluation_result)
        
        # Save evaluation to database
        db_evaluation = DrefEvaluation.objects.create(
            dref_id=dref_id,
            status=evaluation_result.overall_status,
            section_results=response_data['section_results'],
            improvement_suggestions=response_data['improvement_suggestions'],
            reference_examples_used=evaluation_result.reference_examples_used,
            pass_one_completed=evaluation_result.pass_one_completed,
            pass_two_completed=evaluation_result.pass_two_completed,
        )
        
        # Create history entry
        EvaluationHistory.objects.create(
            dref_id=dref_id,
            evaluation=db_evaluation,
            status_snapshot=evaluation_result.overall_status,
            accepted_count=db_evaluation.get_accepted_criteria_count(),
            total_count=sum(
                len(sr.criteria_results) 
                for sr in evaluation_result.section_results.values()
            ),
            trigger='initial'
        )
        
        response_data['evaluation_id'] = db_evaluation.id
        
        return Response(response_data, status=status.HTTP_200_OK)


class AutoImproveView(APIView):
    """
    POST /evaluate/auto-improve
    
    Automatically applies high-priority improvements via the existing /chat endpoint.
    Returns updated form state and new evaluation.
    """
    permission_classes = [AllowAny]  # Adjust as needed
    
    def post(self, request):
        serializer = AutoImproveRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        form_state = serializer.validated_data['form_state']
        dref_id = serializer.validated_data.get('dref_id', 0)
        max_improvements = serializer.validated_data.get('max_improvements', 5)
        
        auto_improver = AutoImprover()
        result = auto_improver.auto_improve(dref_id, form_state, max_improvements)
        
        return Response(result, status=status.HTTP_200_OK)


class SectionEvaluateView(APIView):
    """
    POST /evaluate/section
    
    Evaluates a specific section of the DREF form.
    Used by the "Evaluate" button at the bottom of each section.
    """
    permission_classes = [AllowAny]  # Adjust as needed
    
    def post(self, request):
        serializer = SectionEvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        section_name = serializer.validated_data['section_name']
        form_state = serializer.validated_data['form_state']
        dref_id = serializer.validated_data.get('dref_id', 0)
        
        evaluator = DrefEvaluator()
        
        try:
            section_result = evaluator.evaluate_section(section_name, form_state, dref_id)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate improvement suggestions for this section
        suggestions = []
        for cid, cr in section_result.criteria_results.items():
            if cr.outcome == 'dont_accept':
                suggestions.append({
                    'section': section_name,
                    'field': cr.field,
                    'criterion': cr.criterion,
                    'priority': 1 if cr.required else 2,
                    'guidance': cr.guidance,
                    'ready_prompt': cr.improvement_prompt,
                    'auto_applicable': True
                })
        
        response_data = {
            'section_name': section_result.section_name,
            'section_display_name': section_result.section_display_name,
            'status': section_result.status,
            'criteria_results': {
                cid: {
                    'criterion_id': cr.criterion_id,
                    'field': cr.field,
                    'criterion': cr.criterion,
                    'outcome': cr.outcome,
                    'required': cr.required,
                    'reasoning': cr.reasoning,
                    'improvement_prompt': cr.improvement_prompt,
                    'guidance': cr.guidance,
                }
                for cid, cr in section_result.criteria_results.items()
            },
            'issues': section_result.issues,
            'improvement_suggestions': suggestions
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class RubricView(APIView):
    """
    GET /evaluate/rubric
    
    Returns the evaluation rubric for reference.
    """
    permission_classes = [AllowAny]  # Adjust as needed
    
    def get(self, request):
        rubric = RubricLoader()
        return Response(rubric.rubric, status=status.HTTP_200_OK)


class DrefEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DrefEvaluation records.
    """
    queryset = DrefEvaluation.objects.all()
    serializer_class = DrefEvaluationSerializer
    permission_classes = [AllowAny]  # Adjust as needed
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DrefEvaluationListSerializer
        return DrefEvaluationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by dref_id if provided
        dref_id = self.request.query_params.get('dref_id')
        if dref_id:
            queryset = queryset.filter(dref_id=dref_id)
        
        # Filter by status if provided
        evaluation_status = self.request.query_params.get('status')
        if evaluation_status:
            queryset = queryset.filter(status=evaluation_status)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get evaluation history for a specific evaluation."""
        evaluation = self.get_object()
        history = EvaluationHistory.objects.filter(evaluation=evaluation)
        serializer = EvaluationHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_dref(self, request):
        """Get all evaluations for a specific DREF."""
        dref_id = request.query_params.get('dref_id')
        if not dref_id:
            return Response(
                {'error': 'dref_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluations = self.get_queryset().filter(dref_id=dref_id)
        serializer = DrefEvaluationListSerializer(evaluations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest_by_dref(self, request):
        """Get the latest evaluation for a specific DREF."""
        dref_id = request.query_params.get('dref_id')
        if not dref_id:
            return Response(
                {'error': 'dref_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation = self.get_queryset().filter(dref_id=dref_id).first()
        if not evaluation:
            return Response(
                {'error': 'No evaluation found for this DREF'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DrefEvaluationSerializer(evaluation)
        return Response(serializer.data)


class DrefReferenceExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DrefReferenceExample records.
    """
    queryset = DrefReferenceExample.objects.filter(is_active=True)
    serializer_class = DrefReferenceExampleSerializer
    permission_classes = [AllowAny]  # Adjust as needed
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DrefReferenceExampleListSerializer
        return DrefReferenceExampleSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by disaster_type if provided
        disaster_type = self.request.query_params.get('disaster_type')
        if disaster_type:
            queryset = queryset.filter(disaster_type=disaster_type)
        
        # Filter by region if provided
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search for similar reference examples.
        In a full implementation, this would use vector similarity search.
        """
        disaster_type = request.query_params.get('disaster_type')
        region = request.query_params.get('region')
        operation_type = request.query_params.get('operation_type')
        
        queryset = self.get_queryset()
        
        if disaster_type:
            queryset = queryset.filter(disaster_type__icontains=disaster_type)
        if region:
            queryset = queryset.filter(region__icontains=region)
        if operation_type:
            queryset = queryset.filter(operation_type__icontains=operation_type)
        
        # Return top 5 by quality score
        queryset = queryset.order_by('-quality_score')[:5]
        
        serializer = DrefReferenceExampleListSerializer(queryset, many=True)
        return Response(serializer.data)


class EvaluationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing evaluation history.
    """
    queryset = EvaluationHistory.objects.all()
    serializer_class = EvaluationHistorySerializer
    permission_classes = [AllowAny]  # Adjust as needed
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by dref_id if provided
        dref_id = self.request.query_params.get('dref_id')
        if dref_id:
            queryset = queryset.filter(dref_id=dref_id)
        
        return queryset

