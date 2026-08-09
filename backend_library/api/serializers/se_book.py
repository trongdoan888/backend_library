from typing import ClassVar

from api.models import *
from rest_framework import serializers


# -- Book --
class AuthorSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name"]  # noqa: RUF012


class CategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]  # noqa: RUF012
# Đọc dữ liệu   
class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSimpleSerializer(many=True, read_only=True)
    categories = CategorySimpleSerializer(many=True, read_only=True)
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [  # noqa: RUF012
            'id', 
            'name', 
            'categories', 
            'authors',
            'total', 
            'total_borrowed', 
            'total_error', 
            'content', 
            'remaining',
        ]  
        read_only_fields: ClassVar[tuple] = ('id', 'total_borrowed', 'total_error')
        extra_kwargs: ClassVar[dict] = {
            'categories': {'required': False, 'allow_null': True},
            'authors': {'required': False, 'allow_null': True},
            'content': {'required': False, 'allow_blank': True},
            'total': {'required': False, 'default': 1},
        }

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    def get_remaining(self, obj):
            return obj.total - obj.total_borrowed - obj.total_error

# Ghi dữ liệu
class BookWriteSerializer(serializers.ModelSerializer): 
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all()
    )

    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all()
    )

    class Meta:
        model = Book
        fields = [  "id","name","authors","categories","total","total_borrowed","total_error","content",]  # noqa: RUF012
        read_only_fields = [  "id","total_borrowed","total_error",]  # noqa: RUF012

class UserBookSerializer(serializers.ModelSerializer):
    authors = AuthorSimpleSerializer(
        many=True,
        read_only=True
    )

    categories = CategorySimpleSerializer(
        many=True,
        read_only=True
    )

    remaining = serializers.SerializerMethodField()

    class Meta:
        model = Book

        fields = ["id","name","authors","categories","content","remaining",]  # noqa: RUF012

    def get_remaining(self, obj):
        return (
            obj.total- obj.total_borrowed- obj.total_error
        )