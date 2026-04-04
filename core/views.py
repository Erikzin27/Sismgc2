from django.views import generic
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from io import BytesIO
import os
import zipfile
from django.db.models import Q
from django.urls import reverse_lazy

from core.mixins import AuthenticatedView, AdminOnlyMixin, user_has_role_or_perm
from aves.models import Ave
from lotes.models import Lote
from linhagens.models import Linhagem
from vendas.models import Venda
from incubacao.models import Incubacao
from core.models import ConfiguracaoSistema
from core.forms import ConfiguracaoForm
from core.services.config import get_configuracao_sistema


class GlobalSearchView(AuthenticatedView, generic.TemplateView):
    template_name = "core/search_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        ctx["query"] = q
        can_view_aves = user_has_role_or_perm(self.request.user, "aves.view_ave")
        can_view_lotes = user_has_role_or_perm(self.request.user, "lotes.view_lote")
        can_view_linhagens = user_has_role_or_perm(self.request.user, "linhagens.view_linhagem")
        can_view_vendas = user_has_role_or_perm(self.request.user, "vendas.view_venda")
        can_view_incubacoes = user_has_role_or_perm(self.request.user, "incubacao.view_incubacao")
        if q:
            ctx["aves"] = (
                Ave.objects.select_related("linhagem").filter(
                    Q(codigo_interno__icontains=q) | Q(identificacao__icontains=q) | Q(nome__icontains=q)
                )[:20]
                if can_view_aves
                else []
            )
            ctx["lotes"] = (
                Lote.objects.select_related("linhagem_principal").filter(
                    Q(nome__icontains=q) | Q(codigo__icontains=q)
                )[:20]
                if can_view_lotes
                else []
            )
            ctx["linhagens"] = Linhagem.objects.filter(nome__icontains=q)[:20] if can_view_linhagens else []
            ctx["vendas"] = (
                Venda.objects.select_related("lote", "ave").filter(
                    Q(cliente__icontains=q) | Q(produto__icontains=q)
                )[:20]
                if can_view_vendas
                else []
            )
            ctx["incubacoes"] = (
                Incubacao.objects.filter(Q(codigo__icontains=q) | Q(origem_ovos__icontains=q))[:20]
                if can_view_incubacoes
                else []
            )
        else:
            ctx["aves"] = []
            ctx["lotes"] = []
            ctx["linhagens"] = []
            ctx["vendas"] = []
            ctx["incubacoes"] = []
        ctx["can_view_aves"] = can_view_aves
        ctx["can_view_lotes"] = can_view_lotes
        ctx["can_view_linhagens"] = can_view_linhagens
        ctx["can_view_vendas"] = can_view_vendas
        ctx["can_view_incubacoes"] = can_view_incubacoes
        return ctx


class ConfiguracaoView(AdminOnlyMixin, AuthenticatedView, generic.UpdateView):
    model = ConfiguracaoSistema
    form_class = ConfiguracaoForm
    template_name = "core/configuracoes.html"
    success_url = reverse_lazy("core:configuracoes")
    permission_required = "core.change_configuracaosistema"

    def get_object(self, queryset=None):
        return get_configuracao_sistema()


class AdminAreaView(AdminOnlyMixin, AuthenticatedView, generic.TemplateView):
    template_name = "core/admin_area.html"


class AdminSegurancaView(AdminOnlyMixin, AuthenticatedView, generic.TemplateView):
    template_name = "core/admin_seguranca.html"


class AdminBackupView(AdminOnlyMixin, AuthenticatedView, generic.TemplateView):
    template_name = "core/admin_backup.html"


class AdminIdentidadeView(AdminOnlyMixin, AuthenticatedView, generic.TemplateView):
    template_name = "core/admin_identidade.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = get_configuracao_sistema()
        ctx["form"] = ConfiguracaoForm(instance=obj)
        return ctx

    def post(self, request, *args, **kwargs):
        obj = get_configuracao_sistema()
        form = ConfiguracaoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return self.render_to_response({"form": form, "saved": True})
        return self.render_to_response({"form": form})


class AdminParametrosView(AdminOnlyMixin, AuthenticatedView, generic.TemplateView):
    template_name = "core/admin_parametros.html"


class AdminBackupDBView(AdminOnlyMixin, AuthenticatedView, generic.View):
    def post(self, request, *args, **kwargs):
        db_settings = settings.DATABASES.get("default", {})
        if db_settings.get("ENGINE", "").endswith("sqlite3"):
            db_path = db_settings.get("NAME")
            if not db_path or not os.path.exists(db_path):
                raise Http404("Arquivo do banco não encontrado.")
            filename = f"sismgc-db-{timezone.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
            return FileResponse(open(db_path, "rb"), as_attachment=True, filename=filename)
        raise Http404("Backup automático disponível apenas para SQLite.")


class AdminBackupMediaView(AdminOnlyMixin, AuthenticatedView, generic.View):
    def post(self, request, *args, **kwargs):
        media_root = settings.MEDIA_ROOT
        if not media_root or not os.path.exists(media_root):
            raise Http404("Pasta de mídia não encontrada.")
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(media_root):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, media_root)
                    zf.write(full_path, rel_path)
        buffer.seek(0)
        filename = f"sismgc-media-{timezone.now().strftime('%Y%m%d-%H%M%S')}.zip"
        return FileResponse(buffer, as_attachment=True, filename=filename)
