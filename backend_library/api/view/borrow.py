from collections import defaultdict
from datetime import datetime
from math import ceil
from django.utils import timezone

from api.models import Borrow, BorrowBook
from api.serializers.se_borrow import (
    BorrowSerializer,
    BorrowWriteSerializer,
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

# =========================== QUẢN LÝ MƯỢN TRẢ ================================


class BorrowView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    # =========================== GET ===========================

    def get(self, request):
        id = request.GET.get("id")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        borrows = Borrow.objects.all()

        if id:
            borrows = borrows.filter(id__icontains=id)

        if request.user.role not in ["admin", "libby"]:
            borrows = borrows.filter(user=request.user)

        total = borrows.count()
        total_pages = ceil(total / limit)

        start = (page - 1) * limit
        end = start + limit

        serializer = BorrowSerializer(borrows[start:end], many=True)

        return Response(
            {
                "data": serializer.data,
                "page": page,
                "page_size": limit,
                "total": total,
                "total_pages": total_pages,
            },
            status=status.HTTP_200_OK,
        )

    # =========================== POST ===========================

    def post(self, request):
        # Chỉ admin và libby được mượn sách
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"message": "Bạn không có quyền mượn sách."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BorrowWriteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Dữ liệu không hợp lệ.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_input = datetime.strptime(request.data.get("due_date"), "%Y-%m-%d").date()  # noqa: DTZ007

        if date_input < datetime.now().date():  # noqa: DTZ005
            return Response(
                {"message": ("Ngày hẹn trả sách không được nhỏ hơn ngày hiện tại.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                # Lấy danh sách sách cần mượn
                books_data = serializer.validated_data["books"]

                # ==================================================
                # KIỂM TRA SỐ LƯỢNG SÁCH
                # ==================================================

                # Cộng gộp số lượng theo từng sách trước khi so sánh với
                # số lượng còn lại. Nếu không gộp, client có thể gửi trùng
                # 1 book_id nhiều lần (mỗi lần số lượng nhỏ) để lách qua
                # điều kiện kiểm tra và mượn vượt số lượng thực tế còn lại.
                requested_quantity_by_book = defaultdict(int)
                for item in books_data:
                    requested_quantity_by_book[item["book"]] += item["book_quantity"]

                for book, quantity in requested_quantity_by_book.items():
                    remaining = book.total - book.total_borrowed - book.total_error

                    if remaining < quantity:
                        return Response(
                            {
                                "message": (
                                    f"Sách '{book.name}' không đủ số lượng để mượn. "
                                    f"Chỉ còn {remaining} cuốn trong khi yêu cầu mượn {quantity} cuốn."
                                ),
                                "book_id": str(book.id),
                                "requested_quantity": quantity,
                                "remaining_quantity": remaining,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # ==================================================
                # TẠO PHIẾU MƯỢN
                # ==================================================

                borrow = serializer.save()

                # ==================================================
                # CẬP NHẬT total_borrowed
                # ==================================================

                borrow_books = BorrowBook.objects.filter(borrow=borrow).select_related(
                    "book"
                )

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    quantity = borrow_book.book_quantity

                    book.total_borrowed += quantity
                    book.save()

            # Serializer trả về dữ liệu đầy đủ
            response_serializer = BorrowSerializer(borrow)

            return Response(
                {
                    "message": "Mượn sách thành công.",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:  # noqa: BLE001
            return Response(
                {
                    "message": "Mượn sách thất bại.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # =========================== PUT ===========================

    def put(self, request):
        # Chỉ admin và libby được chỉnh sửa phiếu mượn
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"message": "Bạn không có quyền chỉnh sửa phiếu mượn."},
                status=status.HTTP_403_FORBIDDEN,
            )

        borrow_id = request.data.get("id")

        if not borrow_id:
            return Response(
                {"message": "Vui lòng cung cấp id phiếu mượn."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrow = get_object_or_404(Borrow, id=borrow_id)

        # Lưu lại trạng thái cũ trước khi update để biết đây có phải là
        # lần đầu phiếu mượn được chuyển sang "returned" hay không.
        previous_status = borrow.borrow_status

        serializer = BorrowSerializer(
            borrow,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Dữ liệu không hợp lệ.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        

        with transaction.atomic():
            serializer.save()
            borrow.payment_date = timezone.now().date()
            borrow.save()

            if borrow.borrow_status == "overdue":
                # Nếu trả sách trễ hạn, tính tiền phạt
                if borrow.due_date and borrow.payment_date > borrow.due_date:
                    days_late = (borrow.payment_date - borrow.due_date).days
                    fine_per_day = 10000  # Giả sử tiền phạt là 10.000 VND/ngày
                    borrow.fine_amount = days_late * fine_per_day
                    borrow.save()
                else:
                    borrow.fine_amount = 0
                    borrow.save()

            # Chỉ hoàn trả sách về kho đúng 1 lần: khi trạng thái mới là
            # "returned" và trạng thái trước đó chưa phải "returned".
            # Nếu không có điều kiện previous_status, gọi PUT nhiều lần
            # với borrow_status="returned" sẽ trừ total_borrowed lặp lại
            # nhiều lần, làm sai lệch số lượng sách còn lại.
            if previous_status != "returned" and borrow.borrow_status == "returned":
                borrow_books = BorrowBook.objects.filter(borrow=borrow).select_related(
                    "book"
                )

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    book.total_borrowed = max(
                        0, book.total_borrowed - borrow_book.book_quantity
                    )
                    book.save()

        return Response(
            {
                "message": "Cập nhật phiếu mượn thành công.",
                "data": BorrowSerializer(borrow).data,
            },
            status=status.HTTP_200_OK,
        )

    # =========================== DELETE ===========================

    def delete(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": ("Bạn không có quyền xóa thông tin mượn sách")},
                status=status.HTTP_403_FORBIDDEN,
            )

        id = request.data.get("id")

        try:
            borrow = Borrow.objects.get(id=id)
        except Borrow.DoesNotExist:
            return Response(
                {"error": "Phiếu mượn không tồn tại!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            # Nếu phiếu mượn chưa được trả (chưa "returned") mà đã bị xóa,
            # số sách trong phiếu vẫn đang tính là "đang mượn". Phải cộng
            # trả lại total_borrowed trước khi xóa, nếu không sách sẽ bị
            # kẹt vĩnh viễn ở trạng thái "đang mượn" dù phiếu không còn tồn tại.
            if borrow.borrow_status != "returned":
                borrow_books = BorrowBook.objects.filter(borrow=borrow).select_related(
                    "book"
                )

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    book.total_borrowed = max(
                        0, book.total_borrowed - borrow_book.book_quantity
                    )
                    book.save()

            borrow.delete()

        return Response(
            {"message": ("Đã xóa phiếu mượn thành công!")},
            status=status.HTTP_200_OK,
        )
