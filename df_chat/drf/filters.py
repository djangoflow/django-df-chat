import django_filters.rest_framework

from ..models import Message

class MessageFilter(django_filters.rest_framework.FilterSet):
    created_gte = django_filters.rest_framework.DateTimeFilter(
        field_name="created", lookup_expr="gte")
    created_lte = django_filters.rest_framework.DateTimeFilter(
        field_name="created", lookup_expr="lte")
    # TODO: Maybe a better/cleaner implementation for this?
    username = django_filters.rest_framework.CharFilter(
        field_name="room_user__user__username", lookup_expr="contains")
    # ! This is not efficient. 
    body = django_filters.rest_framework.CharFilter(
        field_name="body", lookup_expr="contains")

    class Meta:
        model = Message
        fields = ()
