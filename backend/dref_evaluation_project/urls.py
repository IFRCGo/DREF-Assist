"""
URL configuration for dref_evaluation_project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/v2/dref-evaluation/', include('dref_evaluation.urls')),
]

