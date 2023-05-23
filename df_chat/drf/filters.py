from django_filters import rest_framework as filters

from ..models import Message

class MessageFilter(filters.FilterSet):
    """
    Filter-set class for `Message` list API.
    All the filters that will be accessible by the filter backend
        are defined here.
    """
    # For `datetime` range filter on the model's `created` field.
    created_gte = filters.DateTimeFilter(
        field_name="created", lookup_expr="gte")
    created_lte = filters.DateTimeFilter(
        field_name="created", lookup_expr="lte")
    
    # For filter on the model's related user's `username` field.
    # TODO: Maybe a better/cleaner implementation for this?
    username = filters.CharFilter(
        field_name="room_user__user__username", lookup_expr="contains")
    
    # For text search on the model's `body` field.
    # ! This is not efficient. Text search is better handled otherwise. 
    body = filters.CharFilter(
        field_name="body", lookup_expr="contains")

    class Meta:
        model = Message
        fields = ()
