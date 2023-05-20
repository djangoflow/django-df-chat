import django_filters.rest_framework

from ..models import Message

class MessageFilter(django_filters.rest_framework.FilterSet):
    created_gte = django_filters.rest_framework.DateTimeFilter(
        field_name="created", lookup_expr='gte')
    created_lte = django_filters.rest_framework.DateTimeFilter(
        field_name="created", lookup_expr='lte')

    class Meta:
        model = Message
        fields = ()
