from datetime import date

from django.http import JsonResponse
from django.views import generic

from core.mixins import AuthenticatedView, user_has_role_or_perm
from sanidade.models import AplicacaoVacina, Medicamento
from incubacao.models import Incubacao
from nascimentos.models import Nascimento
from abate.models import Abate
from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro, OrcamentoFuturo


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    # FullCalendar envia "YYYY-MM-DD" ou "YYYY-MM-DDTHH:MM:SSZ"
    if "T" in value:
        value = value.split("T", 1)[0]
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class CalendarioView(AuthenticatedView, generic.TemplateView):
    template_name = "calendario/index.html"


class CalendarioEventosView(AuthenticatedView, generic.View):
    def get(self, request, *args, **kwargs):
        start_date = _parse_iso_date(request.GET.get("start"))
        end_date = _parse_iso_date(request.GET.get("end"))
        eventos = []
        can_view_vendas = user_has_role_or_perm(request.user, "vendas.view_venda")
        can_view_financeiro = user_has_role_or_perm(request.user, "financeiro.view_lancamentofinanceiro")
        can_view_planejamento = user_has_role_or_perm(request.user, "financeiro.view_orcamentofuturo")

        vacinas_qs = AplicacaoVacina.objects.select_related("vacina").filter(data_programada__isnull=False)
        if start_date:
            vacinas_qs = vacinas_qs.filter(data_programada__gte=start_date)
        if end_date:
            vacinas_qs = vacinas_qs.filter(data_programada__lte=end_date)
        for v in vacinas_qs:
            eventos.append(
                {
                    "title": f"Vacina: {v.vacina}",
                    "start": v.data_programada.isoformat(),
                    "color": "#f5b53e",
                }
            )

        incub_qs = Incubacao.objects.filter(previsao_eclosao__isnull=False)
        if start_date:
            incub_qs = incub_qs.filter(previsao_eclosao__gte=start_date)
        if end_date:
            incub_qs = incub_qs.filter(previsao_eclosao__lte=end_date)
        for i in incub_qs:
            eventos.append(
                {
                    "title": f"Eclosão: {i.codigo}",
                    "start": i.previsao_eclosao.isoformat(),
                    "color": "#2aa6ff",
                }
            )

        nasc_qs = Nascimento.objects.select_related("lote_destino").filter(data__isnull=False)
        if start_date:
            nasc_qs = nasc_qs.filter(data__gte=start_date)
        if end_date:
            nasc_qs = nasc_qs.filter(data__lte=end_date)
        for n in nasc_qs:
            eventos.append(
                {
                    "title": f"Nascimento: {n.lote_destino or 'Sem lote'}",
                    "start": n.data.isoformat(),
                    "color": "#3fb950",
                }
            )

        abate_qs = Abate.objects.select_related("lote").filter(data__isnull=False)
        if start_date:
            abate_qs = abate_qs.filter(data__gte=start_date)
        if end_date:
            abate_qs = abate_qs.filter(data__lte=end_date)
        for a in abate_qs:
            eventos.append(
                {
                    "title": f"Abate: {a.lote or 'Sem lote'}",
                    "start": a.data.isoformat(),
                    "color": "#f85149",
                }
            )

        med_qs = Medicamento.objects.filter(validade__isnull=False)
        if start_date:
            med_qs = med_qs.filter(validade__gte=start_date)
        if end_date:
            med_qs = med_qs.filter(validade__lte=end_date)
        for m in med_qs:
            eventos.append(
                {
                    "title": f"Vencimento: {m.nome}",
                    "start": m.validade.isoformat(),
                    "color": "#d6a354",
                }
            )

        if can_view_vendas:
            venda_qs = Venda.objects.filter(data__isnull=False)
            if start_date:
                venda_qs = venda_qs.filter(data__gte=start_date)
            if end_date:
                venda_qs = venda_qs.filter(data__lte=end_date)
            for v in venda_qs:
                eventos.append(
                    {
                        "title": f"Venda: {v.cliente} - {v.produto}",
                        "start": v.data.isoformat(),
                        "color": "#0ea5a4",
                    }
                )

        if can_view_financeiro:
            pagamentos_qs = LancamentoFinanceiro.objects.filter(tipo=LancamentoFinanceiro.TIPO_SAIDA, data__isnull=False)
            if start_date:
                pagamentos_qs = pagamentos_qs.filter(data__gte=start_date)
            if end_date:
                pagamentos_qs = pagamentos_qs.filter(data__lte=end_date)
            for p in pagamentos_qs:
                eventos.append(
                    {
                        "title": f"Pagamento: {p.descricao}",
                        "start": p.data.isoformat(),
                        "color": "#ff7b72",
                    }
                )

        if can_view_planejamento:
            compras_qs = OrcamentoFuturo.objects.filter(
                data_planejada__isnull=False,
                ativo=True,
            ).exclude(status=OrcamentoFuturo.STATUS_CANCELADO)
            if start_date:
                compras_qs = compras_qs.filter(data_planejada__gte=start_date)
            if end_date:
                compras_qs = compras_qs.filter(data_planejada__lte=end_date)
            for o in compras_qs:
                eventos.append(
                    {
                        "title": f"Planejamento: {o.titulo}",
                        "start": o.data_planejada.isoformat(),
                        "color": "#8a6a3f",
                    }
                )

        return JsonResponse(eventos, safe=False)
