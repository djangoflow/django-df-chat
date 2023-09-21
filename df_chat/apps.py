from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DfModuleConfig(AppConfig):
    name = "df_chat"
    verbose_name = _("DjangoFlow Chat")

    class DFMeta:
        api_path = "chat/"
