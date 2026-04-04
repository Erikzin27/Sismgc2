from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("estoque", "0004_itemestoque_ultimo_preco_movimentoestoque_fornecedor_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="itemestoque",
            index=models.Index(fields=["categoria", "nome"], name="estoque_ite_categor_3c8216_idx"),
        ),
        migrations.AddIndex(
            model_name="itemestoque",
            index=models.Index(fields=["validade"], name="estoque_ite_validad_59a218_idx"),
        ),
        migrations.AddIndex(
            model_name="movimentoestoque",
            index=models.Index(fields=["item", "data"], name="estoque_mov_item_id_f51f97_idx"),
        ),
        migrations.AddIndex(
            model_name="movimentoestoque",
            index=models.Index(fields=["tipo", "data"], name="estoque_mov_tipo_215782_idx"),
        ),
        migrations.AddIndex(
            model_name="movimentoestoque",
            index=models.Index(fields=["lote_relacionado", "data"], name="estoque_mov_lote_re_1fcdec_idx"),
        ),
        migrations.AddIndex(
            model_name="movimentoestoque",
            index=models.Index(fields=["motivo", "data"], name="estoque_mov_motivo_622af0_idx"),
        ),
    ]
