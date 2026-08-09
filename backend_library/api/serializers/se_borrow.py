from typing import ClassVar

from api.models import *
from rest_framework import serializers


# -- Borrow --
class BookSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "name"]  # noqa: RUF012 

class BookQuantitySerializer(serializers.ModelSerializer):
    borrow_id = serializers.ReadOnlyField(source='borrow.id')
    book_id = serializers.ReadOnlyField(source='book.id')
    name = serializers.ReadOnlyField(source='book.name')
    class Meta:
        model = BorrowBook
        fields = ["id","borrow_id","book_id","name","book_quantity",]  # noqa: RUF012

class BorrowSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.name')
    book_quantities = BookQuantitySerializer(source='borrow_books', many=True, read_only=True)
    class Meta:
        model = Borrow
        fields = [  # noqa: RUF012
            'id', 
            'user', 
            'user_name', 
            'book_quantities',
            'borrow_date', 
            'payment_date',
            'due_date', 
            'borrow_status',
            'fine_amount'
        ]  
        read_only_fields: ClassVar[tuple] = ('id', 'borrow_date')
        extra_kwargs: ClassVar[dict] = {
            'due_date': {'required': False, 'allow_null': True},
            'borrow_status': {'required': False},
        }
        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

# --- GHI DỮ LIỆU ---
class BorrowBookWriteSerializer(serializers.Serializer):
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all()
    )
    book_quantity = serializers.IntegerField(
        min_value=1
    )


class BorrowWriteSerializer(serializers.ModelSerializer):
    books = BorrowBookWriteSerializer(
        many=True
    )

    class Meta:
        model = Borrow
        fields = ["id","user","books","borrow_date","payment_date","due_date","borrow_status","fine_amount"]  # noqa: RUF012

        read_only_fields = ["id","borrow_date","payment_date","fine_amount"]  # noqa: RUF012

    def create(self, validated_data):
        books_data = validated_data.pop("books")

        borrow = Borrow.objects.create(
            **validated_data
        )

        for item in books_data:
            BorrowBook.objects.create(
                borrow=borrow,
                book=item["book"],
                book_quantity=item["book_quantity"]
            )

        return borrow

