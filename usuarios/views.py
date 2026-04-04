from django.urls import reverse_lazy
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import generic

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, AdminOnlyMixin, SearchFilterMixin
from .models import User, UserProfile
from .forms import UserCreateForm, UserUpdateForm, UserProfileForm, UserSelfForm


def build_user_queryset(request):
    qs = User.objects.select_related("profile")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    role = request.GET.get("role", "").strip()
    if role:
        qs = qs.filter(role=role)
    is_active = request.GET.get("is_active", "").strip()
    if is_active == "true":
        qs = qs.filter(is_active=True)
    elif is_active == "false":
        qs = qs.filter(is_active=False)
    setor = request.GET.get("setor", "").strip()
    if setor:
        qs = qs.filter(profile__setor__icontains=setor)
    last_login = request.GET.get("last_login", "").strip()
    if last_login == "never":
        qs = qs.filter(last_login__isnull=True)
    elif last_login in {"7", "30", "90"}:
        days = int(last_login)
        since = timezone.now() - timezone.timedelta(days=days)
        qs = qs.filter(last_login__gte=since)
    return qs


class UserListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = User
    template_name = "usuarios/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    permission_required = "usuarios.view_user"
    search_fields = ["username", "first_name", "last_name", "email"]
    filter_fields = ["role", "is_active"]

    def get_queryset(self):
        return build_user_queryset(self.request)


class UserCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "usuarios/user_form.html"
    success_url = reverse_lazy("usuarios:list")
    permission_required = "usuarios.add_user"

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class UserUpdateView(AdminOnlyMixin, AuthenticatedView, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "usuarios/user_form.html"
    success_url = reverse_lazy("usuarios:list")
    permission_required = "usuarios.change_user"


class UserDeleteView(AdminOnlyMixin, AuthenticatedView, generic.DeleteView):
    model = User
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("usuarios:list")
    permission_required = "usuarios.delete_user"


class UserDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = User
    template_name = "usuarios/user_detail.html"
    context_object_name = "user_obj"
    permission_required = "usuarios.view_user"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.object)
        ctx["profile"] = profile
        return ctx


class UserToggleActiveView(AdminOnlyMixin, AuthenticatedView, generic.View):
    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs["pk"])
        user.is_active = not user.is_active
        user.save()
        return self.redirect_back(request)

    def redirect_back(self, request):
        from django.shortcuts import redirect

        return redirect(request.META.get("HTTP_REFERER", "usuarios:list"))


class UserExportExcelView(AdminOnlyMixin, AuthenticatedView, generic.View):
    def get(self, request, *args, **kwargs):
        from openpyxl import Workbook

        qs = build_user_queryset(request)
        wb = Workbook()
        ws = wb.active
        ws.title = "Usuarios"
        headers = [
            "Username",
            "Nome",
            "Email",
            "Perfil",
            "Status",
            "Ultimo acesso",
            "Data criacao",
            "Telefone",
            "Setor",
        ]
        ws.append(headers)
        for u in qs:
            profile = getattr(u, "profile", None)
            ws.append(
                [
                    u.username,
                    u.get_full_name(),
                    u.email,
                    u.get_role_display(),
                    "Ativo" if u.is_active else "Inativo",
                    u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "",
                    u.date_joined.strftime("%Y-%m-%d %H:%M") if u.date_joined else "",
                    profile.telefone if profile else "",
                    profile.setor if profile else "",
                ]
            )
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"usuarios-{timezone.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response


class UserExportPDFView(AdminOnlyMixin, AuthenticatedView, generic.View):
    def get(self, request, *args, **kwargs):
        try:
            from weasyprint import HTML
        except Exception:
            messages.error(
                request,
                "PDF indisponivel. WeasyPrint nao esta instalado ou esta sem dependencias no Windows.",
            )
            from django.shortcuts import redirect

            return redirect(request.META.get("HTTP_REFERER", "usuarios:list"))
        qs = build_user_queryset(request)
        html_string = render_to_string("usuarios/user_report.html", {"users": qs})
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"usuarios-{timezone.now().strftime('%Y%m%d-%H%M%S')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ProfileView(AuthenticatedView, generic.TemplateView):
    template_name = "usuarios/profile.html"

    def _build_forms(self, user, post_data=None, files=None):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return (
            profile,
            UserProfileForm(post_data, files, instance=profile) if post_data is not None else UserProfileForm(instance=profile),
            UserSelfForm(post_data, instance=user) if post_data is not None else UserSelfForm(instance=user),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        _, profile_form, user_form = self._build_forms(self.request.user)
        ctx["profile_form"] = profile_form
        ctx["user_form"] = user_form
        return ctx

    def post(self, request, *args, **kwargs):
        _, profile_form, user_form = self._build_forms(request.user, request.POST, request.FILES)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return self.get(request, *args, **kwargs)
        messages.error(request, "Não foi possível salvar o perfil. Verifique os campos destacados.")
        context = self.get_context_data(**kwargs)
        context["profile_form"] = profile_form
        context["user_form"] = user_form
        return self.render_to_response(context)
