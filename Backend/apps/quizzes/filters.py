import django_filters
from .models import Quiz


class QuizFilter(django_filters.FilterSet):
    topic      = django_filters.NumberFilter(field_name='topic__id')
    difficulty = django_filters.ChoiceFilter(
                     choices=[('easy','Easy'),('medium','Medium'),('hard','Hard')]
                 )
    created_after  = django_filters.DateFilter(
                         field_name='created_at',
                         lookup_expr='gte'
                     )
    created_before = django_filters.DateFilter(
                         field_name='created_at',
                         lookup_expr='lte'
                     )
    is_ai_generated = django_filters.BooleanFilter()

    class Meta:
        model  = Quiz
        fields = ['topic', 'difficulty', 'is_ai_generated']