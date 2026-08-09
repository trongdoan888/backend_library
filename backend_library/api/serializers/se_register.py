from typing import ClassVar

from api.models import *
from rest_framework import serializers


# --- THÊM TÀI KHOẢN ---
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'phone', 'name', 'role']  # noqa: RUF012
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'phone': {'required': False, 'allow_blank': True},
            'name': {'required': False, 'allow_blank': True},
            'role': {'required': False},
            'email': {'required': False, 'allow_blank': True},
        }

    # 🔑 BẮT BUỘC CÓ HÀM NÀY ĐỂ MẬT KHẨU KHÔNG BỊ LƯU DẠNG PLAIN TEXT
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        return User.objects.create_user(
            username=username,
            password=password,
            **validated_data
        )
