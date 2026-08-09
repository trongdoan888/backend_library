from math import ceil

from api.models import Borrow, BorrowBook
from api.serializers.se_borrow import (
    BorrowSerializer,
    BorrowWriteSerializer,
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
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

        serializer = BorrowSerializer(
            borrows[start:end],
            many=True
        )

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
                {
                    "message": "Bạn không có quyền mượn sách."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BorrowWriteSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Dữ liệu không hợp lệ.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():

                # Lấy danh sách sách cần mượn
                books_data = serializer.validated_data["books"]

                # ==================================================
                # KIỂM TRA SỐ LƯỢNG SÁCH
                # ==================================================

                for item in books_data:
                    book = item["book"]
                    quantity = item["book_quantity"]

                    remaining = (
                        book.total
                        - book.total_borrowed
                        - book.total_error
                    )

                    if remaining < quantity:
                        return Response(
                            {
                                "message": (
                                    f"Sách '{book.name}' "
                                    f"không đủ số lượng để mượn."
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

                borrow_books = BorrowBook.objects.filter(
                    borrow=borrow
                ).select_related("book")

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    quantity = borrow_book.book_quantity

                    book.total_borrowed += quantity
                    book.save()

            # Serializer trả về dữ liệu đầy đủ
            response_serializer = BorrowSerializer(
                borrow
            )

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
        # Chỉ admin và libby được trả sách
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {
                    "message": "Bạn không có quyền trả sách."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        FINE_PER_DAY = 10000

        borrow_id = request.data.get("id")

        if not borrow_id:
            return Response(
                {
                    "message": "Vui lòng cung cấp id phiếu mượn."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrow = get_object_or_404(
            Borrow,
            id=borrow_id
        )

        # ==================================================
        # KIỂM TRA ĐÃ TRẢ SÁCH CHƯA
        # ==================================================

        if borrow.payment_date is not None:
            return Response(
                {
                    "message": (
                        "Phiếu mượn đã được trả trước đó."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()

        try:
            with transaction.atomic():

                # ==================================================
                # LẤY CÁC SÁCH TRONG PHIẾU MƯỢN
                # ==================================================

                borrow_books = BorrowBook.objects.filter(
                    borrow=borrow
                ).select_related("book")

                # ==================================================
                # KIỂM TRA total_borrowed
                # ==================================================

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    quantity = borrow_book.book_quantity

                    if book.total_borrowed < quantity:
                        return Response(
                            {
                                "message": (
                                    f"Số lượng sách "
                                    f"'{book.name}' "
                                    f"không hợp lệ."
                                ),
                                "book_id": str(book.id),
                                "currently_borrowed": (
                                    book.total_borrowed
                                ),
                                "return_quantity": quantity,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # ==================================================
                # KIỂM TRA QUÁ HẠN
                # ==================================================

                if today > borrow.due_date:
                    overdue_days = (
                        today - borrow.due_date
                    ).days

                    borrow.borrow_status = "overdue"

                    borrow.fine_amount = (
                        overdue_days * FINE_PER_DAY
                    )

                else:
                    borrow.borrow_status = "returned"
                    borrow.fine_amount = 0

                # ==================================================
                # PAYMENT DATE
                # ==================================================

                borrow.payment_date = today

                # ==================================================
                # CẬP NHẬT total_borrowed
                # ==================================================

                for borrow_book in borrow_books:
                    book = borrow_book.book
                    quantity = borrow_book.book_quantity

                    book.total_borrowed -= quantity
                    book.save()

                # Lưu phiếu mượn
                borrow.save()

            serializer = BorrowSerializer(borrow)

            return Response(
                {
                    "message": "Trả sách thành công.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:  # noqa: BLE001
            return Response(
                {
                    "message": "Trả sách thất bại.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # =========================== DELETE ===========================

    def delete(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {
                    "error": (
                        "Bạn không có quyền xóa "
                        "thông tin mượn sách"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        id = request.data.get("id")

        try:
            borrow = Borrow.objects.get(id=id)
            borrow.delete()

            return Response(
                {
                    "message": (
                        "Đã xóa phiếu mượn thành công!"
                    )
                },
                status=status.HTTP_200_OK,
            )

        except Borrow.DoesNotExist:
            return Response(
                {
                    "error": "Phiếu mượn không tồn tại!"
                },
                status=status.HTTP_404_NOT_FOUND,
            )