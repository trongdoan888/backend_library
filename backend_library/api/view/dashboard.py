from api.models import Book, Borrow, User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


# --- 3. DASHBOARD (Chỉ dành riêng cho Admin) ---
class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]  # noqa: RUF012
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        # Chỉ Admin mới có quyền xem Dashboard
        if request.user.role != "admin":
            return Response(
                {"error": "Trang này chỉ dành cho Admin!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            total_books = Book.objects.count()
            total_users = User.objects.count()
            total_borrowed = Borrow.objects.filter(borrow_status="borrowed").count()
            total_overdue = Borrow.objects.filter(borrow_status="overdue").count()

            return Response(
                {
                    "total_books": total_books,
                    "total_users": total_users,
                    "total_borrowed": total_borrowed,
                    "total_overdue": total_overdue,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
