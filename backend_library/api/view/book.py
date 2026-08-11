
from math import ceil

from api.models import Book
from api.serializers.se_book import (
    BookSerializer,
    BookWriteSerializer,
    UserBookSerializer,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# =========================QUẢN LÝ SÁCH ========================================
class BookView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    # --- 1. LẤY DANH SÁCH SÁCH ---
    def get(self, request):
        name = request.GET.get("name")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        books = Book.objects.all()

        # Phân trang 
        if name:
            books = books.filter(name__icontains=name)

        total = books.count()
        total_pages = ceil(total / limit)

        start = (page - 1) * limit
        end = start + limit

        if request.user.role in ["admin", "libby"]:
            serializer = BookSerializer(books[start:end], many=True)
        else:
            serializer = UserBookSerializer(books[start:end], many=True)

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
    # --- 2. THÊM SÁCH MỚI ---
    def post(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Không đủ quyền!"},
                status=status.HTTP_403_FORBIDDEN
            )

        if Book.objects.filter(
            name=request.data.get("name")
        ).exists():
            return Response(
                {"error": "Tên sách bị trùng!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookWriteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        book = serializer.save()

        return Response(
            {
                "message": "Thêm sách thành công!",
                "book": BookSerializer(book).data
            },
            status=status.HTTP_201_CREATED
        )
    # --- 3. CẬP NHẬT SÁCH ---
    def put(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response({
                "error": "Không đủ quyền truy cập!"
            }, status = status.HTTP_403_FORBIDDEN,)

        id = request.data.get("id")

        try:
            book = Book.objects.get(id=id)
        except Book.DoesNotExist:
            return Response({
                "error": "Sách không tồn tại!"
            }, status = status.HTTP_404_NOT_FOUND,)

        name = request.data.get("name")
        if name and Book.objects.filter(name=name).exclude(id=id).exists():
            return Response({
                "error": "Tên sách đã tồn tại!"
            }, status = status.HTTP_400_BAD_REQUEST,)

        serializer = BookWriteSerializer(book, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "error": serializer.errors,
            }, status = status.HTTP_400_BAD_REQUEST,)

        serializer.save()

        return Response({
            "message": "Cập nhật sách thành công!",
            "book": BookSerializer(book).data,
        }, status = status.HTTP_200_OK,)
    # --- 4. XÓA SÁCH ---
    def delete(self, request):
        if request.user.role in ["admin", "libby"]:
            id = request.data.get("id")

            try:
                book = Book.objects.get(id=id)
                book.delete()
                return Response(
                    {"message": "Đã xóa sách khỏi kho."}, status=status.HTTP_200_OK
                )
            except Book.DoesNotExist:
                return Response(
                    {"error": "Sách không tồn tại."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"error": "Không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

