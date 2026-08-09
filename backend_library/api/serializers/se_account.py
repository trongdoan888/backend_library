from typing import ClassVar

from api.models import *
from rest_framework import serializers


# -- User --
class UserSerializer(serializers.ModelSerializer):
    # 1. Khai báo thuộc tính password
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        min_length=6, 
        allow_blank=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'phone', 'role', 'name']  # noqa: RUF012
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'phone': {'required': False, 'allow_blank': True},
            'name': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'role': {'required': False},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

    


