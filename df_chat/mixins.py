class IdStringRepresentationSerializerMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = str(data.get("id", instance.pk))
        return data
