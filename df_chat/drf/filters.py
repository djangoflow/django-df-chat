from django_filters import rest_framework as filters

from ..models import Message

class MessageFilter(filters.FilterSet):
    """
    Filter-set class for `Message` list API.
    """
    created_gte = filters.DateTimeFilter(
        field_name="created", lookup_expr="gte")
    created_lte = filters.DateTimeFilter(
        field_name="created", lookup_expr="lte")
    
    username = filters.CharFilter(
        field_name="room_user__user__username", lookup_expr="contains")
    
    body = filters.CharFilter(
        field_name="body", lookup_expr="contains")

    class Meta:
        model = Message
        fields = ()
