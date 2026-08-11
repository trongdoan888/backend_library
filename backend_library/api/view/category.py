from math import ceil

from api.models import Category
from api.serializers.se_category import (
    CategorySerializer,
)
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# --- 2. QUẢN LÝ LOẠI SÁCH ---
class CategoryView(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        if request.user.role in ["admin", "libby"]:
            name = request.GET.get("name")
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))

            categories = Category.objects.all()

            if name:
                categories = categories.filter(name__icontains=name)

            total = categories.count()
            total_pages = ceil(total / limit)

            start = (page - 1) * limit
            end = start + limit

            serializer = CategorySerializer(categories[start:end], many=True)

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
            name = request.GET.get("name")
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))

            categories = Category.objects.all()

            if name:
                categories = categories.filter(name__icontains=name)

            total = categories.count()
            total_pages = ceil(total / limit)

            start = (page - 1) * limit
            end = start + limit

            serializer = CategorySerializer(categories[start:end], many=True)

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


    def post(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Không đủ quyền truy cập!"}, status=status.HTTP_403_FORBIDDEN
            )
        try:
            serializer = CategorySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Dữ liệu không hợp lệ."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Category.objects.filter(name=request.data.get("name")).exists():
                return Response(
                    {
                        "error": "Tên loại sách bị trùng!",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                try:
                    serializer.save()
                except Exception as e:  # noqa: BLE001
                    print(e)
                    return Response(
                        {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(
                {"message": "Thêm loại sách thành công!", "category": serializer.data},
                status=status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response(
                {"error": "Mã loại sách đã tồn tại!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def put(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Không đủ quyền truy cập!"}, status=status.HTTP_403_FORBIDDEN
            )
        id = request.data.get("id")
        try:
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response(
                {"error": "Loại sách không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Cập nhật loại sách thành công.",
                    "category": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Dữ liệu không hợp lệ.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Không đủ quyền truy cập!"}, status=status.HTTP_403_FORBIDDEN
            )
        id = request.data.get("id")
        try:
            category = Category.objects.get(id=id)
            category.delete()
            return Response(
                {"message": "Đã xóa loại sách khỏi kho."}, status=status.HTTP_200_OK
            )
        except Category.DoesNotExist:
            return Response(
                {"error": "Loại sách không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )
