from django.apps import AppConfig


class DrefEvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dref_evaluation'
    verbose_name = 'DREF Quality Evaluation'
    
    def ready(self):
        pass

