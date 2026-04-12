from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone

from estoque.models import MovimentoEstoque


def consumo_medio_item(item, dias=30):
    if not item:
        return 0
    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=dias)
    total = (
        MovimentoEstoque.objects.filter(
            item=item, tipo=MovimentoEstoque.TIPO_SAIDA, data__gte=inicio, data__lte=hoje
        ).aggregate(total=Sum("quantidade"))["total"]
        or 0
    )
    dias_base = max(dias, 1)
    return total / dias_base


def dias_restantes_item(item, consumo_medio):
    if not item or not consumo_medio:
        return None
    if consumo_medio <= 0:
        return None
    return (item.quantidade_atual or 0) / consumo_medio


def gerar_sugestoes(alertas, limite=6):
    sugestoes = []
    for item in alertas.get("estoque_critico", [])[:3]:
        sugestoes.append(
            f"Estoque de {item['item']} acaba em {item['dias_restantes']} dia(s)."
        )
    vacinas = list(alertas.get("vacinas_atrasadas", [])[:3])
    for vac in vacinas:
        dias = getattr(vac, "dias_atraso", None)
        dias_txt = f" ha {dias} dia(s)" if dias is not None else ""
        sugestoes.append(f"Vacina {vac.vacina} atrasada{dias_txt}.")
    contas_vencidas = alertas.get("contas_vencidas", [])
    if hasattr(contas_vencidas, "count") and contas_vencidas.count() > 0:
        sugestoes.append(f"Voce tem {contas_vencidas.count()} contas vencidas.")
    contas_proximas = alertas.get("contas_proximas", [])
    if hasattr(contas_proximas, "count") and contas_proximas.count() > 0:
        sugestoes.append(f"Existem {contas_proximas.count()} contas vencendo nos proximos dias.")
    lotes = alertas.get("lotes_problema", [])
    try:
        total_lotes = lotes.count()
    except TypeError:
        total_lotes = len(lotes)
    if total_lotes > 0:
        sugestoes.append("Ha lotes com mortalidade alta ou inconsistencias.")
    return sugestoes[:limite]
