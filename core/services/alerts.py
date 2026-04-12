from datetime import timedelta
from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from estoque.models import ItemEstoque
from sanidade.models import AplicacaoVacina, Medicamento, Tratamento
from incubacao.models import Incubacao
from lotes.models import Lote
from financeiro.models import LancamentoFinanceiro
from core.services.insights import consumo_medio_item, dias_restantes_item


ALERTA_JANELA_DIAS = 30
ALERTA_ESTOQUE_DIAS = 7
ALERTA_CONTAS_DIAS = 7


def _empty_like(value):
    if hasattr(value, "none"):
        return value.none()
    return []


def filtrar_alertas_por_perfil(alertas, user):
    try:
        from core.mixins import user_has_role_or_perm
    except Exception:
        return alertas

    if not user or not user.is_authenticated:
        return {}

    # Estoque
    if not user_has_role_or_perm(user, "estoque.view_itemestoque"):
        alertas["estoque_baixo"] = _empty_like(alertas.get("estoque_baixo"))
        alertas["estoque_critico"] = []
        alertas["itens_vencidos"] = _empty_like(alertas.get("itens_vencidos"))

    # Sanidade
    if not user_has_role_or_perm(user, ["sanidade.view_vacina", "sanidade.view_tratamento"]):
        alertas["vacinas_pendentes"] = _empty_like(alertas.get("vacinas_pendentes"))
        alertas["vacinas_atrasadas"] = _empty_like(alertas.get("vacinas_atrasadas"))
        alertas["medicamentos_vencendo"] = _empty_like(alertas.get("medicamentos_vencendo"))
        alertas["carencias_ativas"] = []

    # Incubação
    if not user_has_role_or_perm(user, "incubacao.view_incubacao"):
        alertas["incubacoes_proximas"] = _empty_like(alertas.get("incubacoes_proximas"))
        alertas["nascimentos_previstos"] = _empty_like(alertas.get("nascimentos_previstos"))

    # Financeiro
    if not user_has_role_or_perm(user, "financeiro.view_lancamentofinanceiro"):
        alertas["contas_vencidas"] = _empty_like(alertas.get("contas_vencidas"))
        alertas["contas_proximas"] = _empty_like(alertas.get("contas_proximas"))

    # Lotes
    if not user_has_role_or_perm(user, "lotes.view_lote"):
        alertas["lotes_problema"] = _empty_like(alertas.get("lotes_problema"))

    return alertas


def get_alertas(user=None):
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=ALERTA_JANELA_DIAS)

    cache_key = "sismgc:alertas:base"
    alertas_base = cache.get(cache_key)
    if alertas_base is None:
        estoque_baixo = ItemEstoque.objects.filter(quantidade_atual__lte=F("estoque_minimo"))
        estoque_critico = []
        for item in ItemEstoque.objects.all():
            consumo = consumo_medio_item(item, dias=30)
            dias_restantes = dias_restantes_item(item, consumo)
            if dias_restantes is not None and dias_restantes <= ALERTA_ESTOQUE_DIAS:
                estoque_critico.append(
                    {
                        "item": item,
                        "dias_restantes": round(dias_restantes, 1),
                    }
                )
        vacinas_pendentes = AplicacaoVacina.objects.select_related("vacina", "ave", "lote").filter(
            status=AplicacaoVacina.STATUS_PENDENTE
        )
        vacinas_atrasadas = vacinas_pendentes.filter(data_programada__lt=hoje)
        medicamentos_vencendo = Medicamento.objects.filter(validade__isnull=False, validade__lte=limite)
        itens_vencidos = ItemEstoque.objects.filter(validade__isnull=False, validade__lt=hoje)
        incubacoes_proximas = Incubacao.objects.filter(
            status=Incubacao.STATUS_EM_ANDAMENTO, previsao_eclosao__isnull=False, previsao_eclosao__lte=limite
        )
        nascimentos_previstos = Incubacao.objects.filter(
            status=Incubacao.STATUS_EM_ANDAMENTO, previsao_eclosao__isnull=False, previsao_eclosao__lte=limite
        )
        contas_vencidas = LancamentoFinanceiro.objects.filter(
            tipo=LancamentoFinanceiro.TIPO_SAIDA, data__lt=hoje
        )
        contas_proximas = LancamentoFinanceiro.objects.filter(
            tipo=LancamentoFinanceiro.TIPO_SAIDA, data__gte=hoje, data__lte=hoje + timedelta(days=ALERTA_CONTAS_DIAS)
        )
        lotes_problema = []
        for lote in Lote.objects.filter(status=Lote.STATUS_ATIVO):
            if lote.mortalidade_percentual >= 10:
                lotes_problema.append(lote)
        carencias_ativas = []
        for tratamento in Tratamento.objects.select_related("medicamento", "ave", "lote").filter(data_fim__isnull=False):
            if tratamento.carencia_ativa:
                carencias_ativas.append(tratamento)

        alertas_base = {
            "estoque_baixo": estoque_baixo,
            "estoque_critico": estoque_critico,
            "vacinas_pendentes": vacinas_pendentes,
            "vacinas_atrasadas": vacinas_atrasadas,
            "medicamentos_vencendo": medicamentos_vencendo,
            "itens_vencidos": itens_vencidos,
            "incubacoes_proximas": incubacoes_proximas,
            "nascimentos_previstos": nascimentos_previstos,
            "contas_vencidas": contas_vencidas,
            "contas_proximas": contas_proximas,
            "lotes_problema": lotes_problema,
            "carencias_ativas": carencias_ativas,
            "janela_dias": ALERTA_JANELA_DIAS,
        }
        cache.set(cache_key, alertas_base, 8)

    alertas = alertas_base.copy()
    if user is not None:
        return filtrar_alertas_por_perfil(alertas, user)
    return alertas
