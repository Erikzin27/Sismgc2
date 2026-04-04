from historico.models import HistoricoEvento


def registrar_evento(entidade, referencia_id, descricao, usuario=None, acao="update", detalhes=None):
    HistoricoEvento.objects.create(
        entidade=entidade,
        referencia_id=referencia_id,
        descricao=descricao,
        usuario=usuario,
        acao=acao,
        detalhes=detalhes or {},
    )
