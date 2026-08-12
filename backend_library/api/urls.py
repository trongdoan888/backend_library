from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.view.account import Account, UserView
from api.view.author import AuthorView
from api.view.book import BookView
from api.view.borrow import BorrowView
from api.view.category import CategoryView
from api.view.dashboard import DashboardView
from api.view.login import LockoutTokenObtainPairView, LoginCheck

urlpatterns = [
    path("api/token/", LockoutTokenObtainPairView.as_view(), name="token_obtain_view"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh_view"),
    path("api/check_login/", LoginCheck.as_view(), name="check_login"),
    path("api/account/", Account.as_view(), name="account"),
    path("api/user/", UserView.as_view(), name="user"),
    path("api/book/", BookView.as_view(), name="book"),
    path("api/borrow/", BorrowView.as_view(), name="borrow"),
    path("api/author/", AuthorView.as_view(), name="author"),
    path("api/category/", CategoryView.as_view(), name="category"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
]
