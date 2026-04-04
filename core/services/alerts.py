from datetime import timedelta
from django.db.models import F
from django.utils import timezone

from estoque.models import ItemEstoque
from sanidade.models import AplicacaoVacina, Medicamento, Tratamento
from incubacao.models import Incubacao


ALERTA_JANELA_DIAS = 30


def get_alertas():
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=ALERTA_JANELA_DIAS)

    estoque_baixo = ItemEstoque.objects.filter(quantidade_atual__lte=F("estoque_minimo"))
    vacinas_pendentes = AplicacaoVacina.objects.select_related("vacina", "ave", "lote").filter(
        status=AplicacaoVacina.STATUS_PENDENTE
    )
    medicamentos_vencendo = Medicamento.objects.filter(validade__isnull=False, validade__lte=limite)
    incubacoes_proximas = Incubacao.objects.filter(
        status=Incubacao.STATUS_EM_ANDAMENTO, previsao_eclosao__isnull=False, previsao_eclosao__lte=limite
    )
    nascimentos_previstos = Incubacao.objects.filter(
        status=Incubacao.STATUS_EM_ANDAMENTO, previsao_eclosao__isnull=False, previsao_eclosao__lte=limite
    )
    carencias_ativas = []
    for tratamento in Tratamento.objects.select_related("medicamento", "ave", "lote").filter(data_fim__isnull=False):
        if tratamento.carencia_ativa:
            carencias_ativas.append(tratamento)

    return {
        "estoque_baixo": estoque_baixo,
        "vacinas_pendentes": vacinas_pendentes,
        "medicamentos_vencendo": medicamentos_vencendo,
        "incubacoes_proximas": incubacoes_proximas,
        "nascimentos_previstos": nascimentos_previstos,
        "carencias_ativas": carencias_ativas,
        "janela_dias": ALERTA_JANELA_DIAS,
    }
