import django_filters.rest_framework as filters

from . import models


class TestChildModelFilter(filters.FilterSet):
    parent = filters.CharFilter(
        method='parent_filter',
    )

    def parent_filter(self, queryset, name, value):
        return queryset.filter(parent__name=value)

    class Meta:
        fields = '__all__'
        model = models.TestChildModel
