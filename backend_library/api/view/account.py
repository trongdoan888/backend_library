from math import ceil

from api.models import User
from api.serializers.se_account import (
    UserSerializer,
)
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


class Account(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    # --- 1. LẤY THÔNG TIN TÀI KHOẢN ---
    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


# =========================QUẢN LÝ TÀI KHOẢN ======================================
class UserView(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    # --- 1. LẤY THÔNG TIN TÀI KHOẢN ---
    def get(self, request):
        if request.user.role in ["admin", "libby"]:
            name = request.GET.get("name")
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))

            users = User.objects.all()

            # Libby chỉ được xem các tài khoản vai trò user
            if request.user.role == "libby":
                users = users.filter(role="user")

            # Phân trang
            if name:
                users = users.filter(name__icontains=name)

            total = users.count()
            total_pages = ceil(total / limit)

            start = (page - 1) * limit
            end = start + limit

            serializer = UserSerializer(users[start:end], many=True)

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
                "username": request.user.username,
                "name": request.user.name,
                "email": request.user.email,
                "phone": request.user.phone,
            }
            return Response(data, status=status.HTTP_200_OK)

    # --- 2. TẠO TÀI KHOẢN MỚI ---
    def post(self, request):
        if request.user.role in ["admin", "libby"]:
            serializer = UserSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Dữ liệu không hợp lệ."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(username=request.data.get("username")).exists():
                return Response(
                    {
                        "error": "Tên tài khoản bị trùng!",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                serializer.save()
                return Response(
                    {"message": "Tạo tài khoản thành công!", "user": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError:
                return Response(
                    {"error": " Username / Email đã tồn tại."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:  # noqa: BLE001
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {"error": "Bạn không có quyền tạo tài khoản!"},
                status=status.HTTP_403_FORBIDDEN,
            )

    # --- 3. CẬP NHẬT TÀI KHOẢN ---
    def put(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Bạn không đủ quyền!"}, status=status.HTTP_403_FORBIDDEN
            )

        if "role" in request.data and request.user.role != "admin":
            return Response(
                {"error": "Chỉ Admin mới có quyền sửa vai trò người dùng!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        id = request.data.get("id")
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {"error": "Tài khoản không tồn tại."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "is_active" in request.data and request.user.role == "libby" and user.role == "admin":
            return Response(
                {"error": "Libby không có quyền khóa/mở khóa tài khoản Admin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Cập nhật tài khoản thành công!",
                    "user": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Dữ liệu không hợp lệ.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- 4. XÓA TÀI KHOẢN ---
    def delete(self, request):
        if request.user.role not in ["admin", "libby"]:
            return Response(
                {"error": "Chỉ Admin hoặc Libby mới có quyền xóa tài khoản!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        id = request.data.get("id")

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {"error": "Tài khoản không tồn tại."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "libby" and user.role == "admin":
            return Response(
                {"error": "Libby không có quyền xóa tài khoản Admin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.delete()
        return Response(
            {"message": "Đã xóa tài khoản thành công."},
            status=status.HTTP_200_OK,
        )
