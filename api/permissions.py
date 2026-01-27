from rest_framework.permissions import BasePermission


class IsCreator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "CREATOR"


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "MANAGER"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "SUPER_ADMIN"
