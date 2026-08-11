from api.models import Book, Borrow, User
from django.db.models import Sum
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
            # Đồng bộ trạng thái quá hạn trước khi thống kê để total_overdue
            # phản ánh đúng thực tế thay vì chỉ dựa vào giá trị lưu sẵn.
            Borrow.sync_all_overdue()

            total_books = Book.objects.count()
            total_book_quantity = Book.objects.aggregate(total=Sum("total"))["total"] or 0
            total_users = User.objects.count()
            # Số lượng sách (bản) đang được mượn, không phải số phiếu mượn
            total_borrowed = Book.objects.aggregate(total=Sum("total_borrowed"))["total"] or 0
            total_overdue = Borrow.objects.filter(borrow_status="overdue").count()

            return Response(
                {
                    "total_books": total_books,
                    "total_book_quantity": total_book_quantity,
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
