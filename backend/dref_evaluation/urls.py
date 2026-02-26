from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluateView,
    AutoImproveView,
    SectionEvaluateView,
    RubricView,
    DrefEvaluationViewSet,
    DrefReferenceExampleViewSet,
    EvaluationHistoryViewSet,
    AIEvaluateView,
    AISuggestionsView,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'evaluations', DrefEvaluationViewSet, basename='evaluation')
router.register(r'reference-examples', DrefReferenceExampleViewSet, basename='reference-example')
router.register(r'history', EvaluationHistoryViewSet, basename='evaluation-history')

# URL patterns
urlpatterns = [
    # Main evaluation endpoints
    path('evaluate/', EvaluateView.as_view(), name='evaluate'),
    path('evaluate/auto-improve/', AutoImproveView.as_view(), name='auto-improve'),
    path('evaluate/section/', SectionEvaluateView.as_view(), name='evaluate-section'),
    path('evaluate/rubric/', RubricView.as_view(), name='rubric'),
    path('ai-evaluate/', AIEvaluateView.as_view(), name='ai-evaluate'),
    path('ai-suggestions/', AISuggestionsView.as_view(), name='ai-suggestions'),
    
    # ViewSet routes
    path('', include(router.urls)),
]

# API endpoint summary:
# POST /evaluate/                    - Full DREF evaluation
# POST /evaluate/auto-improve/       - Auto-improve with chat integration
# POST /evaluate/section/            - Section-level evaluation
# GET  /evaluate/rubric/             - Get evaluation rubric
#
# GET/POST   /evaluations/           - List/Create evaluations
# GET/PUT/DELETE /evaluations/{id}/  - Retrieve/Update/Delete evaluation
# GET  /evaluations/{id}/history/    - Get history for evaluation
# GET  /evaluations/by_dref/         - Get evaluations by DREF ID
# GET  /evaluations/latest_by_dref/  - Get latest evaluation for DREF
#
# GET/POST   /reference-examples/    - List/Create reference examples
# GET/PUT/DELETE /reference-examples/{id}/ - Retrieve/Update/Delete reference
# GET  /reference-examples/search/   - Search similar references
#
# GET  /history/                     - List evaluation history
# GET  /history/{id}/                - Get history entry

