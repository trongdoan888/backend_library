from typing import ClassVar

from rest_framework import serializers

from .models import *


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


        
# -- Category --
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'name': {'required': True},
        }

# -- Author --
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'
        read_only_fields: ClassVar[tuple] = ('id',)
        extra_kwargs: ClassVar[dict] = {
            'name': {'required': True},
        }


# -- Book --
class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    author_name = serializers.ReadOnlyField(source='author.name')

    class Meta:
        model = Book
        fields = [  # noqa: RUF012
            'id', 
            'name', 
            'category', 
            'category_name',
            'author', 
            'author_name',
            'total', 
            'total_borrowed', 
            'total_error', 
            'content', 
        ]  
        read_only_fields: ClassVar[tuple] = ('id', 'total_borrowed', 'total_error')
        extra_kwargs: ClassVar[dict] = {
            'category': {'required': False, 'allow_null': True},
            'author': {'required': False, 'allow_null': True},
            'content': {'required': False, 'allow_blank': True},
            'total': {'required': False, 'default': 1},
        }

# -- Borrow --
class BorrowSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.name')
    book_name = serializers.ReadOnlyField(source='book.name')

    class Meta:
        model = Borrow
        fields = [  # noqa: RUF012
            'id', 
            'user', 
            'user_name', 
            'book', 
            'book_name', 
            'borrow_date', 
            'due_date', 
            'borrow_status'
        ]  
        read_only_fields: ClassVar[tuple] = ('id', 'borrow_date')
        extra_kwargs: ClassVar[dict] = {
            'due_date': {'required': False, 'allow_null': True},
            'borrow_status': {'required': False},
        }

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
