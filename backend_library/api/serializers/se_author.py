from typing import ClassVar

from api.models import *
from rest_framework import serializers


# -- Author --
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
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

class UserAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']  # noqa: RUF012
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'name': {'required': True},
        }
