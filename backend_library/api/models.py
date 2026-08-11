import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


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

    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

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
    authors = models.ManyToManyField(
        Author,
        related_name="books",
        blank=True,
    )

    categories = models.ManyToManyField(
        Category,
        related_name="books",
        blank=True,
    )
    total = models.IntegerField(default=0)
    total_borrowed = models.IntegerField(default=0)
    total_error = models.IntegerField(default=0)
    content = models.TextField(default="")

    def __str__(self):
        return self.id

# Mượn sách 
class Borrow(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    borrow_date = models.DateField(auto_now_add=True)

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

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    FINE_PER_DAY = 10000  # Tiền phạt mỗi ngày trễ hạn (VND)

    def calculate_fine(self, reference_date=None):
        """Tính tiền phạt dựa trên số ngày trễ so với due_date.

        reference_date mặc định là payment_date (nếu đã trả) hoặc ngày hiện
        tại (nếu sách vẫn đang được mượn) để phản ánh đúng số tiền phạt đang
        phát sinh tại thời điểm tính.
        """
        reference_date = reference_date or self.payment_date or timezone.now().date()

        if self.due_date and reference_date > self.due_date:
            days_late = (reference_date - self.due_date).days
            return days_late * self.FINE_PER_DAY

        return 0

    def sync_overdue_status(self):
        """Tự động cập nhật borrow_status sang 'overdue' và tính lại
        fine_amount nếu đã quá due_date mà vẫn chưa trả sách.

        Không tác động tới các phiếu đã 'returned'. Trả về True nếu
        borrow_status hoặc fine_amount có thay đổi (chưa lưu vào DB).
        """
        if self.borrow_status == "returned":
            return False

        today = timezone.now().date()
        new_status = "overdue" if self.due_date and today > self.due_date else "borrowed"
        new_fine = self.calculate_fine(reference_date=today)

        changed = new_status != self.borrow_status or new_fine != self.fine_amount
        self.borrow_status = new_status
        self.fine_amount = new_fine
        return changed

    @classmethod
    def sync_all_overdue(cls):
        """Quét toàn bộ phiếu mượn chưa trả và tự động chuyển sang 'overdue'
        kèm tính lại tiền phạt nếu đã quá hạn trả sách."""
        borrows = list(cls.objects.exclude(borrow_status="returned"))
        changed_borrows = [borrow for borrow in borrows if borrow.sync_overdue_status()]

        if changed_borrows:
            cls.objects.bulk_update(changed_borrows, ["borrow_status", "fine_amount"])

    def __str__(self):
        return str(self.id)


class BorrowBook(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    borrow = models.ForeignKey(
        Borrow,
        on_delete=models.CASCADE,
        related_name="borrow_books"
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    book_quantity = models.IntegerField(
        default=1
    )

    def __str__(self):
        return str(self.id)
