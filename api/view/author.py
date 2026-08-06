from math import ceil

from api.models import Author
from api.serializers import (
    AuthorSerializer,
)
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# --- 1. QUẢN LÝ TÁC GIẢ ---
class AuthorView(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        if request.user.role in ["admin", "libby"]:
            name = request.GET.get("name")
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("page", 10))

            authors = Author.objects.all()

            # Phân trang 
            if name:
                authors = authors.filter(name__icontains=name)

            total = authors.count()
            total_pages = ceil(total / limit)

            start = (page - 1) * limit
            end = start + limit

            serializer = AuthorSerializer(authors[start:end], many=True)

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
            data = {
                "name": request.author.name,
            }
            return Response(data, status)

    def post(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Bạn không có quyền thêm tác giả!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AuthorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"Error": "Dữ liệu không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if Author.objects.filter(name = request.data.get("name")).exists():
                return Response({
                    "Error" :  "Tên tác giả bị trùng!",
                })
            
            serializer.save()
            return Response(
                {"message": "Thêm tác giả thành công!", "author": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {"error": "Mã tác giả đã tồn tại!"}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Bạn không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

        id = request.data.get("id")
        try:
            author = Author.objects.get(id=id)
            serializer = AuthorSerializer(author, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Cập nhật thành công", "author": serializer.data},
                    status=status.HTTP_200_OK,
            )
        except Author.DoesNotExist:
            return Response(
                {"error": "Tác giả không tồn tại!"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Bạn không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

        id = request.data.get("id")
        try:
            author = Author.objects.get(id=id)
            author.delete()
            return Response(
                {"message": "Đã xóa tác giả thành công!"}, status=status.HTTP_200_OK
            )
        except Author.DoesNotExist:
            return Response(
                {"error": "Tác giả không tồn tại!"}, status=status.HTTP_404_NOT_FOUND
            )
