from django.db.models.signals import post_save
from django.dispatch import receiver

from historico.services import registrar_evento
from core.threadlocal import get_current_user
from aves.models import Ave
from lotes.models import Lote
from vendas.models import Venda
from abate.models import Abate
from sanidade.models import AplicacaoVacina, Tratamento
from estoque.models import MovimentoEstoque


@receiver(post_save, sender=Ave)
def historico_ave(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Ave", instance.pk, f"Ave {acao}", user, acao)


@receiver(post_save, sender=Lote)
def historico_lote(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Lote", instance.pk, f"Lote {acao}", user, acao)


@receiver(post_save, sender=Venda)
def historico_venda(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Venda", instance.pk, f"Venda {acao}", user, acao)


@receiver(post_save, sender=Abate)
def historico_abate(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Abate", instance.pk, f"Abate {acao}", user, acao)


@receiver(post_save, sender=AplicacaoVacina)
def historico_vacina(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Vacina", instance.pk, f"Aplicação de vacina {acao}", user, acao)


@receiver(post_save, sender=Tratamento)
def historico_tratamento(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Tratamento", instance.pk, f"Tratamento {acao}", user, acao)


@receiver(post_save, sender=MovimentoEstoque)
def historico_estoque(sender, instance, created, **kwargs):
    user = get_current_user()
    acao = "create" if created else "update"
    registrar_evento("Estoque", instance.pk, f"Movimento de estoque {acao}", user, acao)
