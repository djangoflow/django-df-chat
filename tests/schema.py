from drf_spectacular.openapi import AutoSchema as DefaultAutoSchema
from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    field = serializers.CharField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    errors = ErrorSerializer(many=True, required=True)


class AutoSchema(DefaultAutoSchema):
    def get_response_serializers(self):
        response_serializers = (
            self.view.response_serializer_class
            if hasattr(self.view, "response_serializer_class")
            else super().get_response_serializers()
        )

        responses = {"400": ErrorResponseSerializer}

        if self.method == "DELETE":
            responses["204"] = None
        elif self._is_create_operation():
            responses["201"] = response_serializers
        else:
            responses["200"] = response_serializers
        return responses
