from rest_framework import permissions

class IsPlannerOrReadOnly(permissions.BasePermission):
    """
    Faqat planner va admin foydalanuvchilar yozish/ozgartirish huquqiga ega.
    Boshqa foydalanuvchilar faqat o'qishi mumkin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Yozish/ozgartirish/ochirish
        return request.user.is_authenticated and request.user.role in [
            "planner",
            "admin",
        ]
class IsWarehouseHeadOrReadOnly(permissions.BasePermission):
    """
    Faqat warehouse_head va admin foydalanuvchilar yozish/ozgartirish huquqiga ega.
    Boshqa foydalanuvchilar faqat o'qishi mumkin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Yozish/ozgartirish/ochirish
        return request.user.is_authenticated and request.user.role in [
            "warehouse_head",
            "admin",
        ]
