from rest_framework import serializers

from .models import GroundObject, Image


class ImageSerializer(serializers.ModelSerializer):
    """Serializer to convert Image objects to JSON"""

    class Meta:
        model = Image
        fields = "__all__"


class GroundObjectSerializer(serializers.ModelSerializer):
    """Serializer to convert GroundObject objects to JSON"""

    class Meta:
        model = GroundObject
        fields = "__all__"
