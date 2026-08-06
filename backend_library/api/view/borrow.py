from datetime import timezone
from math import ceil

from api.models import Book, Borrow, User
from api.serializers import (
    BorrowSerializer,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

# ===========================QUẢN LÝ MƯỢN TRẢ ================================


class BorrowView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    # 1. GET: Lấy danh sách mượn trả
    def get(self, request):
        name = request.GET.get("name")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("page", 10))

        borrrows = Borrow.objects.all()

        # Phân trang
        if name:
            borrrows = borrrows.filter(name__icontains=name)

        if request.user.role not in ["admin", "libby"]:
            borrrows = borrrows.filter(user=request.user)

        total = borrrows.count()
        total_pages = ceil(total / limit)

        start = (page - 1) * limit
        end = start + limit

        serializer = BorrowSerializer(borrrows[start:end], many=True)

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

    # 2. POST: Mượn sách
    def post(self, request):
        book_id = request.data.get("book")
        user_id = (
            request.data.get("user")
            if request.user.role in ["admin", "libby"]
            else request.user.user
        )

        try:
            user_obj = User.objects.get(user=user_id)
            book_obj = Book.objects.get(book_id=book_id)
        except (User.DoesNotExist, Book.DoesNotExist):
            return Response(
                {"error": "Người dùng hoặc Sách không tồn tại."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        available_books = book_obj.total - (
            book_obj.total_borrowed + book_obj.total_error
        )
        if available_books <= 0:
            return Response(
                {"error": f"Sách '{book_obj.book_name}' đã hết trong kho!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        id = request.data.get("id")
        borrow_date = request.data.get("borrow_date", timezone.now().date())
        due_date = request.data.get("due_date")

        if not id or not due_date:
            return Response(
                {"error": "Vui lòng nhập borrow_id và due_date."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_borrow = Borrow.objects.create(
            user=user_obj,
            book=book_obj,
            borrow_date=borrow_date,
            due_date=due_date,
            borrow_status="borrowed",
        )

        book_obj.total_borrowed += 1
        book_obj.save()

        serializer = BorrowSerializer(new_borrow)
        return Response(
            {"message": "Mượn sách thành công!", "borrow": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    # 3. PUT: Trả sách / Cập nhật trạng thái
    def put(self, request):
        if request.user.role in ["admin", "libby"]:
            id = request.data.get("id")
            new_status = request.data.get("borrow_status")

            try:
                borrow_obj = Borrow.objects.get(id=id)
            except Borrow.DoesNotExist:
                return Response(
                    {"error": "Phiếu mượn không tồn tại."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if borrow_obj.borrow_status != "returned" and new_status == "returned":
                book_obj = borrow_obj.book
                if book_obj.total_borrowed > 0:
                    book_obj.total_borrowed -= 1
                    book_obj.save()

            borrow_obj.borrow_status = new_status
            borrow_obj.save()

            serializer = BorrowSerializer(borrow_obj)
            return Response(
                {
                    "message": "Cập nhật trạng thái thành công.",
                    "borrow": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

    # 4. DELETE: Xóa phiếu mượn
    def delete(self, request):
        if request.user.role in ["admin", "libby"]:
            id = request.data.get("id")

            if not id:
                return Response(
                    {"error": "Vui lòng cung cấp borrow_id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                borrow_obj = Borrow.objects.get(id=id)

                if borrow_obj.borrow_status == "borrowed":
                    book_obj = borrow_obj.book
                    if book_obj.total_borrowed > 0:
                        book_obj.total_borrowed -= 1
                        book_obj.save()

                borrow_obj.delete()
                return Response(
                    {"message": "Đã xóa phiếu mượn thành công."},
                    status=status.HTTP_200_OK,
                )

            except Borrow.DoesNotExist:
                return Response(
                    {"error": "Phiếu mượn không tồn tại."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {"error": "Không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )
