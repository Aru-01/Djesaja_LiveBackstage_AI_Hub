from django.contrib import admin
from ai_insights.models import (
    AIDailySummary,
    AIMessage,
    AIMetric,
    AIScenario,
    AITarget,
    AIManagerTarget,
)

# Register your models here.
admin.site.register(AIDailySummary)
admin.site.register(AIMessage)
admin.site.register(AIMetric)
admin.site.register(AIScenario)
admin.site.register(AITarget)
admin.site.register(AIManagerTarget)
