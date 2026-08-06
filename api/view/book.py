
from math import ceil

from api.models import Author, Book, Category
from api.serializers import (
    BookSerializer,
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
        if request.user.role in ["admin", "libby"]:
                    name = request.GET.get("name")
                    page = int(request.GET.get("page", 1))
                    limit = int(request.GET.get("page", 10))
        
                    books = Book.objects.all()
        
                    # Phân trang 
                    if name:
                        books = books.filter(name__icontains=name)
        
                    total = books.count()
                    total_pages = ceil(total / limit)
        
                    start = (page - 1) * limit
                    end = start + limit
        
                    serializer = BookSerializer(books[start:end], many=True)
        
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
        else:
            data = [
                {
                    "name": book.name,
                    "author": book.author.name if book.author else None,
                    "category": book.category.name if book.category else None,
                    "content": getattr(book, "content", ""),
                }
                for book in books
            ]
            return Response(data, status=status.HTTP_200_OK)

    # --- 2. THÊM SÁCH MỚI ---
    def post(self, request):
        if request.user.role in ["admin", "libby"]:

            serializer = BookSerializer(data=request.data)
            #Kiểm tra có điền đúng form không
            if not serializer.is_valid():
                return Response({
                    "Error": "Dữ liệu không hợp lệ!",
                })
            
            if Book.objects.filter(name = request.data.get('name')):
                return Response({
                    "Error" : "Tên sách bị trùng !"
                }, status=status.HTTP_400_BAD_REQUEST,)

            try:
                    serializer.save()
                    return Response(
                        {"message": "Thêm sách thành công!", "book": serializer.data},
                        status=status.HTTP_201_CREATED,
                    )
            except (Category.DoesNotExist, Author.DoesNotExist):
                return Response(
                    {"error": "Thể loại hoặc Tác giả không tồn tại."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:  # noqa: BLE001
                print(e)
                return Response(
                    {"error": "Mã sách đã tồn tại."}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

    # --- 3. CẬP NHẬT SÁCH ---
    def put(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response({
                "error": "Không đủ quyền truy cập!"
            }, status = status.HTTP_200_OK,)
        
        id = request.data.get("id")

        try:
            book = Book.objects.get(id=id)
            serializer = BookSerializer(book, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Cập nhật loại sách thành công.",
                        "category": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                        )
        except Book.DoesNotExist:
            return Response(
                {"error": "Sách không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            if request.data.get("category"):
                book.category = Category.objects.get(
                    id=request.data.get("category")
                )
            if request.data.get("author"):
                book.author = Author.objects.get(
                    id=request.data.get("author")
                )
        except (Category.DoesNotExist, Author.DoesNotExist):
            return Response(
                {"error": "Thể loại hoặc Tác giả không tồn tại."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        book.save()
        serializer = BookSerializer(book)
        return Response(
            {
                "message": "Cập nhật thông tin sách thành công.",
                "book": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

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

