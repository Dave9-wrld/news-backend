from rest_framework.permissions import BasePermission

from .models import Profile


def is_editor(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser or getattr(getattr(user, 'profile', None), 'role', None) == Profile.Role.EDITOR))


def is_author(user):
    return bool(user and user.is_authenticated and (is_editor(user) or getattr(getattr(user, 'profile', None), 'role', None) == Profile.Role.AUTHOR))


class IsAuthor(BasePermission):
    def has_permission(self, request, view):
        return is_author(request.user)


class IsEditor(BasePermission):
    def has_permission(self, request, view):
        return is_editor(request.user)
