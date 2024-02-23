from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DfModuleConfig(AppConfig):
    name = "df_chat"
    verbose_name = _("DjangoFlow Chat")

    def ready(self) -> None:
        from df_chat import signals  # NoQA

    class DFMeta:
        api_path = "chat/"
