from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from df_chat.models import ChatRoom, ChatMessage


@method_decorator([login_required,], name="dispatch")
class Chat(TemplateView):
    template_name = 'test_app/chat.html'

    def get_context_data(self, *args, **kwargs):
        newest = ChatMessage.objects.filter(chat_group=OuterRef("pk")).order_by("-created_at")
        chat_rooms = ChatRoom.objects.filter(
            users=self.request.user
        ).annotate(newest_message=Subquery(newest.values("message")[:1]))
        context = super().get_context_data(*args, **kwargs)
        context["chat_rooms"] = chat_rooms
        return context
