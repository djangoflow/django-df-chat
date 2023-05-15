from django.contrib.auth import get_user_model

import pytest


User = get_user_model()

pytestmark = [pytest.mark.django_db]


...
