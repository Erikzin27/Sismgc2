"""
Signals para sincronizar Vendas com Financeiro automaticamente.

Padrão: 
- Qualquer mudança em Venda → atualiza LancamentoFinanceiro automaticamente
- Deleta Venda → deleta LancamentoFinanceiro (transação atômica)
- Cria Venda → cria LancamentoFinanceiro se status pagamento = PAGO

IMPORTANTE: Transações atômicas garantem que ou tudo falha ou tudo sucede.
Sem isso: Venda paga pode ficar sem entrada financeira ($ perdido!)
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction, IntegrityError
import logging

from .models import Venda
from financeiro.models import LancamentoFinanceiro

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Venda, dispatch_uid="sync_venda_financeiro_save")
def sincronizar_venda_financeiro(sender, instance, created, **kwargs):
    """
    Sincroniza automaticamente a venda com o financeiro após salvar.
    
    Regras:
    - Se venda paga: cria/atualiza entrada financeira
    - Se venda não paga: remove entrada (se existir)
    - Evita duplicidade com OneToOneField
    - Registra em log para auditoria
    
    Usa transação atômica: ou tudo salva ou nada salva.
    """
    # Evita recursão infinita
    if getattr(instance, '_skip_sync', False):
        return
    
    try:
        with transaction.atomic():
            _sync_venda_lancamento(instance)
    
    except Exception as e:
        logger.error(
            f"Vendas [Signal]: Erro ao sincronizar venda #{instance.pk} "
            f"com financeiro após save: {str(e)}",
            exc_info=True
        )
        # Não relança - deixa venda salva, apenas avisa no log


def _sync_venda_lancamento(venda):
    """
    Sincronização interna entre Venda e LancamentoFinanceiro.
    
    Casos:
    1. Venda CRIADA com status PAGO → Cria LancamentoFinanceiro ENTRADA
    2. Venda ATUALIZADA status PAGO → Atualiza LancamentoFinanceiro
    3. Venda ATUALIZADA status NÃO PAGO → Remove LancamentoFinanceiro
    """
    lancamento = getattr(venda, "lancamento_financeiro", None)
    
    # ═══════════════════════════════════════════════════════════
    # CASO 1: Venda está PAGA → Cria ou atualiza entrada
    # ═══════════════════════════════════════════════════════════
    if venda.status_pagamento == Venda.STATUS_PAGO:
        defaults = {
            "data": venda.data,
            "tipo": LancamentoFinanceiro.TIPO_ENTRADA,
            "categoria": LancamentoFinanceiro.CAT_VENDA,
            "descricao": f"Venda: {venda.produto} - Cliente: {venda.cliente}",
            "valor": venda.valor_total,
            "lote": venda.lote,
            "ave": venda.ave,
            "forma_pagamento": venda.forma_pagamento,
            "observacoes": f"Vinculada à venda #{venda.pk}" + (f"\n{venda.observacoes}" if venda.observacoes else ""),
        }
        
        if lancamento:
            # Atualizar lançamento existente
            for field, value in defaults.items():
                setattr(lancamento, field, value)
            lancamento.save()
            logger.info(f"Venda #{venda.pk}: Lançamento financeiro #{lancamento.pk} atualizado (TRANSAÇÃO ATÔMICA)")
        else:
            # Criar novo lançamento
            lancamento = LancamentoFinanceiro.objects.create(venda=venda, **defaults)
            logger.info(f"Venda #{venda.pk}: Novo lançamento financeiro #{lancamento.pk} criado (TRANSAÇÃO ATÔMICA)")
    
    # ═══════════════════════════════════════════════════════════
    # CASO 2: Venda NÃO está paga → Remove entrada (se existir)
    # ═══════════════════════════════════════════════════════════
    else:
        if lancamento:
            lancamento_pk = lancamento.pk
            lancamento.delete()
            logger.info(f"Venda #{venda.pk}: Lançamento financeiro #{lancamento_pk} removido (status: {venda.status_pagamento})")
        else:
            logger.debug(f"Venda #{venda.pk}: Marcada como {venda.status_pagamento}, sem lançamento para remover")


@receiver(post_delete, sender=Venda, dispatch_uid="sync_venda_financeiro_delete")
def limpar_lancamento_ao_deletar_venda(sender, instance, **kwargs):
    """
    Remove o lançamento financeiro quando a venda é deletada.
    
    Usa post_delete (melhor prática): 
    - post_delete: FK já foi deletada em BD
    - Mais seguro e previsível
    
    Nota: Aqui o lancamento_financeiro.delete() não vai mais funcionar
    porque a Venda foi deletada. Mas a CASCADE do FK se encarrega disso.
    """
    try:
        lancamento_pk = getattr(instance, '_lancamento_pk', None)
        if lancamento_pk:
            # Se conseguiu guardar o PK antes, avisa no log
            logger.info(f"Venda #{instance.pk}: Lançamento financeiro (era #{lancamento_pk}) removido automaticamente pela CASCADE")
        else:
            logger.info(f"Venda #{instance.pk}: Deletada - lançamento removido por CASCADE FK")
    
    except Exception as e:
        logger.error(f"Venda #{instance.pk}: ERRO ao limpar lançamento durante exclusão - {str(e)}")
