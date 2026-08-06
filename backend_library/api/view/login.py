
from api.serializers import (
    RegisterSerializer,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


class LoginCheck(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get(self, request):
        name = request.user.name
        email = request.user.email
        role = request.user.role

        data = {
            'name': name,
            'email': email,
            'role': role,
        }
        return Response(data)

class RegisterView(APIView):
    permission_classes = [] # Cho phép chưa đăng nhập vẫn gọi được API này

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Đăng ký tài khoản thành công!",
                "user": {
                    "id": str(user.id), 
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)