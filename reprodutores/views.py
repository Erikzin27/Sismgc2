from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.mixins import AuthenticatedView, AdminManagerOrPermMixin, SearchFilterMixin
from .models import Reprodutor, Casal
from .forms import ReprodutorForm, CasalForm
from aves.models import Ave


# ============================================
# REPRODUTOR VIEWS
# ============================================

class ReprodutorListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Reprodutor
    template_name = "reprodutores/reprodutor_list.html"
    context_object_name = "reprodutores"
    paginate_by = 20
    permission_required = "reprodutores.view_reprodutor"
    search_fields = ["ave__codigo_interno", "ave__nome"]
    filter_fields = ["tipo", "status", "qualidade_genetica"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("ave", "ave__lote_atual", "ave__linhagem")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        resumo = queryset.aggregate(
            total=Count("id"),
            matrizes=Count("id", filter=Q(tipo=Reprodutor.TIPO_MATRIZ)),
            reprodutores=Count("id", filter=Q(tipo=Reprodutor.TIPO_REPRODUTOR)),
            ativos=Count("id", filter=Q(status=Reprodutor.STATUS_ATIVO, ativo=True)),
            descanso=Count("id", filter=Q(status=Reprodutor.STATUS_DESCANSO)),
            superior=Count("id", filter=Q(qualidade_genetica=Reprodutor.QUALIDADE_SUPERIOR)),
        )
        
        ctx.update(resumo)
        ctx["resumo"] = resumo
        return ctx


class ReprodutorDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Reprodutor
    template_name = "reprodutores/reprodutor_detail.html"
    context_object_name = "reprodutor"
    permission_required = "reprodutores.view_reprodutor"

    def get_queryset(self):
        return super().get_queryset().select_related("ave", "ave__lote_atual", "ave__linhagem", "ave__pai", "ave__mae")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        reprodutor = self.object
        
        # Casais
        if reprodutor.tipo == Reprodutor.TIPO_MATRIZ:
            ctx["casais"] = reprodutor.casais_como_femea.all()
        else:
            ctx["casais"] = reprodutor.casais_como_macho.all()
        
        # Filhotes se existir registro genético
        from genetica.models import RegistroGenetico
        if reprodutor.tipo == Reprodutor.TIPO_REPRODUTOR:
            ctx["filhotes_como_pai"] = RegistroGenetico.objects.filter(
                pai=reprodutor.ave
            ).select_related("filho").count()
        else:
            ctx["filhotes_como_mae"] = RegistroGenetico.objects.filter(
                mae=reprodutor.ave
            ).select_related("filho").count()
        
        return ctx


class ReprodutorCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Reprodutor
    form_class = ReprodutorForm
    template_name = "reprodutores/reprodutor_form.html"
    success_url = reverse_lazy("reprodutores:list")
    permission_required = "reprodutores.add_reprodutor"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Reprodutor '{self.object}' cadastrado com sucesso.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erro ao cadastrar reprodutor. Verifique os campos destacados.")
        return super().form_invalid(form)


class ReprodutorUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Reprodutor
    form_class = ReprodutorForm
    template_name = "reprodutores/reprodutor_form.html"
    success_url = reverse_lazy("reprodutores:list")
    permission_required = "reprodutores.change_reprodutor"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Reprodutor '{self.object}' atualizado com sucesso.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erro ao atualizar reprodutor. Verifique os campos destacados.")
        return super().form_invalid(form)


class ReprodutorDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Reprodutor
    template_name = "reprodutores/confirm_delete.html"
    success_url = reverse_lazy("reprodutores:list")
    permission_required = "reprodutores.delete_reprodutor"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        reprodutor_str = str(self.object)
        messages.success(request, f"Reprodutor '{reprodutor_str}' excluído com sucesso.")
        return super().delete(request, *args, **kwargs)


# ============================================
# CASAL VIEWS
# ============================================

class CasalListView(AdminManagerOrPermMixin, SearchFilterMixin, AuthenticatedView, generic.ListView):
    model = Casal
    template_name = "reprodutores/casal_list.html"
    context_object_name = "casais"
    paginate_by = 20
    permission_required = "reprodutores.view_casal"
    search_fields = ["reprodutor_macho__ave__codigo_interno", "matriz_femea__ave__codigo_interno"]
    filter_fields = ["status"]

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "reprodutor_macho", "reprodutor_macho__ave",
            "matriz_femea", "matriz_femea__ave",
            "lote"
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        resumo = queryset.aggregate(
            total=Count("id"),
            ativos=Count("id", filter=Q(status=Casal.STATUS_ATIVO, ativo=True)),
            pausados=Count("id", filter=Q(status=Casal.STATUS_PAUSADO)),
            finalizados=Count("id", filter=Q(status=Casal.STATUS_CONCLUIDO)),
        )
        
        # Listar lotes para filtro
        from lotes.models import Lote
        ctx["lotes"] = Lote.objects.all().order_by("nome")
        
        ctx.update(resumo)
        ctx["resumo"] = resumo
        return ctx


class CasalDetailView(AdminManagerOrPermMixin, AuthenticatedView, generic.DetailView):
    model = Casal
    template_name = "reprodutores/casal_detail.html"
    context_object_name = "casal"
    permission_required = "reprodutores.view_casal"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "reprodutor_macho", "reprodutor_macho__ave",
            "matriz_femea", "matriz_femea__ave",
            "lote"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        casal = self.object
        
        # Filhotes deste casal através de registro genético
        from genetica.models import RegistroGenetico
        filhotes_qs = RegistroGenetico.objects.filter(
            pai=casal.reprodutor_macho.ave,
            mae=casal.matriz_femea.ave
        ).select_related("filho").order_by("-created_at")
        
        ctx["filhotes_count"] = filhotes_qs.count()
        ctx["ultimos_filhotes"] = filhotes_qs[:5]
        
        return ctx


class CasalCreateView(AdminManagerOrPermMixin, AuthenticatedView, generic.CreateView):
    model = Casal
    form_class = CasalForm
    template_name = "reprodutores/casal_form.html"
    success_url = reverse_lazy("reprodutores:casal_list")
    permission_required = "reprodutores.add_casal"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Casal '{self.object}' cadastrado com sucesso.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erro ao cadastrar casal. Verifique os campos destacados.")
        return super().form_invalid(form)


class CasalUpdateView(AdminManagerOrPermMixin, AuthenticatedView, generic.UpdateView):
    model = Casal
    form_class = CasalForm
    template_name = "reprodutores/casal_form.html"
    success_url = reverse_lazy("reprodutores:casal_list")
    permission_required = "reprodutores.change_casal"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Casal '{self.object}' atualizado com sucesso.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Erro ao atualizar casal. Verifique os campos destacados.")
        return super().form_invalid(form)


class CasalDeleteView(AdminManagerOrPermMixin, AuthenticatedView, generic.DeleteView):
    model = Casal
    template_name = "reprodutores/confirm_delete.html"
    success_url = reverse_lazy("reprodutores:casal_list")
    permission_required = "reprodutores.delete_casal"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        casal_str = str(self.object)
        messages.success(request, f"Casal '{casal_str}' excluído com sucesso.")
        return super().delete(request, *args, **kwargs)


# ============================================
# DASHBOARD
# ============================================

class DashboardReprodutivyView(AdminManagerOrPermMixin, AuthenticatedView, generic.TemplateView):
    template_name = "reprodutores/dashboard.html"
    permission_required = "reprodutores.view_reprodutor"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Agregações de Reprodutores
        reprodutores_qs = Reprodutor.objects.select_related("ave")
        reprodutores_stats = reprodutores_qs.aggregate(
            total=Count("id"),
            matrizes=Count("id", filter=Q(tipo=Reprodutor.TIPO_MATRIZ)),
            machos=Count("id", filter=Q(tipo=Reprodutor.TIPO_REPRODUTOR)),
            ativos=Count("id", filter=Q(ativo=True, status=Reprodutor.STATUS_ATIVO)),
            superior=Count("id", filter=Q(qualidade_genetica=Reprodutor.QUALIDADE_SUPERIOR)),
        )
        
        # Agregações de Casais
        casais_qs = Casal.objects.select_related("reprodutor_macho", "matriz_femea", "reprodutor_macho__ave", "matriz_femea__ave")
        casais_stats = casais_qs.aggregate(
            total=Count("id"),
            ativos=Count("id", filter=Q(status=Casal.STATUS_ATIVO, ativo=True)),
            planejados=Count("id", filter=Q(status=Casal.STATUS_PLANEJADO)),
        )
        
        # Reprodutores destaque (superior)
        reprodutores_destacados = reprodutores_qs.filter(
            qualidade_genetica=Reprodutor.QUALIDADE_SUPERIOR,
            tipo=Reprodutor.TIPO_REPRODUTOR,
            status=Reprodutor.STATUS_ATIVO
        ).annotate(
            casais_count=Count("casais_como_macho", filter=Q(casais_como_macho__ativo=True))
        )[:5]
        
        # Matrizes destaque
        matrizes_destacadas = reprodutores_qs.filter(
            qualidade_genetica=Reprodutor.QUALIDADE_SUPERIOR,
            tipo=Reprodutor.TIPO_MATRIZ,
            status=Reprodutor.STATUS_ATIVO
        ).annotate(
            casais_count=Count("casais_como_femea", filter=Q(casais_como_femea__ativo=True))
        )[:5]
        
        # Casais recentes (últimos 30 dias)
        from django.utils.timezone import now, timedelta
        data_limite = now() - timedelta(days=30)
        casais_recentes = casais_qs.filter(
            data_inicio__gte=data_limite
        ).order_by("-data_inicio")[:10]
        
        ctx.update({
            "reprodutores_total": reprodutores_stats["total"],
            "casais_total": casais_stats["total"],
            "casais_ativos": casais_stats["ativos"],
            "reprodutores_superior": reprodutores_stats["superior"],
            "reprodutores_destacados": reprodutores_destacados,
            "matrizes_destacadas": matrizes_destacadas,
            "casais_recentes": casais_recentes,
        })
        
        return ctx
