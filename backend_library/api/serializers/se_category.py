from typing import ClassVar

from api.models import *
from rest_framework import serializers


# -- Category --
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'name': {'required': True},
        }
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
