from rest_framework.permissions import BasePermission


class IsLibbyAccount(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "libby"


class IsAdminAccount(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"