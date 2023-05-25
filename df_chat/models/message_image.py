from django.db import models

from model_utils.models import TimeStampedModel

from df_chat.models import Message


class MessageImage(TimeStampedModel):
    def get_upload_to(self, filename):
        return f"images/messages/{self.message.id}/{filename}"

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=get_upload_to, height_field="height", width_field="width")
    width = models.IntegerField(default=500)
    height = models.IntegerField(default=300)

    def __str__(self):
        return self.image.url

