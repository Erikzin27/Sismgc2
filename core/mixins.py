from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin


def user_has_role_or_perm(user, permission=None):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "is_admin", False) or getattr(user, "is_manager", False):
        return True
    if permission:
        if isinstance(permission, (list, tuple, set)):
            return user.has_perms(permission)
        return user.has_perm(permission)
    return True


class SearchFilterMixin:
    search_fields = []
    filter_fields = []

    def get_search_query(self):
        return self.request.GET.get("q")

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.get_search_query()
        if query and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            qs = qs.filter(q_objects)
        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                qs = qs.filter(**{field: value})
        return qs


class AuthenticatedView(LoginRequiredMixin):
    pass


class AccessDeniedLogMixin:
    def _log_access_denied(self, motivo, tipo):
        try:
            from historico.models import HistoricoEvento
        except Exception:
            return
        user = getattr(self.request, "user", None)
        usuario = user if user and user.is_authenticated else None
        path = getattr(self.request, "path", "")
        ip = self.request.META.get("HTTP_X_FORWARDED_FOR") or self.request.META.get("REMOTE_ADDR")
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        HistoricoEvento.objects.create(
            entidade="Permissao",
            referencia_id=0,
            acao="status",
            descricao=f"Acesso negado: {path}",
            detalhes={
                "motivo": motivo,
                "tipo": tipo,
                "path": path,
                "ip": ip,
                "user_agent": user_agent,
            },
            usuario=usuario,
        )


class RoleRequiredMixin(AccessDeniedLogMixin, PermissionRequiredMixin):
    """Wrapper for readability; use Django permissions per model."""

    raise_exception = True

    def has_permission(self):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated and user.is_superuser:
            return True
        return super().has_permission()

    def handle_no_permission(self):
        self._log_access_denied("Permissão necessária", "permission_required")
        messages.error(self.request, "Acesso negado. Você não tem permissão para acessar esta área.")
        return super().handle_no_permission()


class AdminManagerOrPermMixin(AccessDeniedLogMixin, PermissionRequiredMixin):
    raise_exception = True

    def has_permission(self):
        user = getattr(self.request, "user", None)
        return user_has_role_or_perm(user, self.get_permission_required())

    def handle_no_permission(self):
        self._log_access_denied("Admin/Gerente necessário", "admin_manager_or_perm")
        messages.error(self.request, "Acesso restrito. Esta área é exclusiva para administradores ou gerentes.")
        return super().handle_no_permission()


class ManagerOrAdminMixin(AccessDeniedLogMixin, UserPassesTestMixin, LoginRequiredMixin):
    raise_exception = True

    def test_func(self):
        user = getattr(self.request, "user", None)
        return bool(user and user.is_authenticated and user.is_manager)

    def handle_no_permission(self):
        self._log_access_denied("Admin/Gerente necessário", "manager_or_admin")
        messages.error(self.request, "Acesso restrito. Esta área é exclusiva para administradores ou gerentes.")
        return super().handle_no_permission()


class AdminOnlyMixin(AccessDeniedLogMixin, UserPassesTestMixin, LoginRequiredMixin):
    raise_exception = True

    def test_func(self):
        user = getattr(self.request, "user", None)
        return bool(user and user.is_authenticated and user.is_admin)

    def handle_no_permission(self):
        self._log_access_denied("Admin necessário", "admin_only")
        messages.error(self.request, "Acesso restrito. Apenas administradores podem entrar aqui.")
        return super().handle_no_permission()
