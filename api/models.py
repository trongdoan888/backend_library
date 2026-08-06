import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


# 1. Định nghĩa Custom Manager dành cho AbstractBaseUser
class CustomUserManager(BaseUserManager):
    # 1. Chuyển tham số bắt buộc từ email thành username
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Tên đăng nhập (username) là bắt buộc')
        
        # Nếu có email 
        if extra_fields.get('email'):
            extra_fields['email'] = self.normalize_email(extra_fields['email'])
        
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)

        # Khởi tạo user với username
        user = self.model(username=username, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(username, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=100, default=None, unique=True)
    phone = models.CharField(max_length=10, default="")

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("user", "User"),
        ("libby", "Libby"),
    )
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default="user")
    name = models.CharField(max_length=100, default="Unknown", blank=True)

    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]  # noqa: RUF012

    def __str__(self):
        return self.id


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Unknown", blank=True)

    def __str__(self):
        return self.id


class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Unknown", blank=True)

    def __str__(self):
        return self.id


class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Unknown", blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null = True, default=None)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null = True, default=None)
    total = models.IntegerField(default=0)
    total_borrowed = models.IntegerField(default=0)
    total_error = models.IntegerField(default=0)
    content = models.TextField(default="")

    def __str__(self):
        return self.id


class Borrow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default="")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, default="")
    borrow_date = models.DateField()
    borrow_status = models.CharField(
        max_length=25,
        choices=[
            ("borrowed", "Borrowed"),
            ("returned", "Returned"),
            ("overdue", "Overdue"),
        ],
        default="borrowed",
    )
    due_date = models.DateField()

    def __str__(self):
        return self.id


class Fines(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    borrow = models.ForeignKey(Borrow, on_delete=models.CASCADE, default="")
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.id
