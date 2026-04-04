from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0005_lancamentofinanceiro_venda"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="lancamentofinanceiro",
            index=models.Index(fields=["tipo", "data"], name="financeiro__tipo_244d6d_idx"),
        ),
        migrations.AddIndex(
            model_name="lancamentofinanceiro",
            index=models.Index(fields=["categoria", "data"], name="financeiro__categor_3c8dbf_idx"),
        ),
        migrations.AddIndex(
            model_name="lancamentofinanceiro",
            index=models.Index(fields=["lote", "data"], name="financeiro__lote_id_4909cf_idx"),
        ),
        migrations.AddIndex(
            model_name="lancamentofinanceiro",
            index=models.Index(fields=["venda"], name="financeiro__venda_i_340fc8_idx"),
        ),
        migrations.AddIndex(
            model_name="orcamentofuturo",
            index=models.Index(fields=["status", "prioridade", "ativo"], name="financeiro__status_0764c1_idx"),
        ),
        migrations.AddIndex(
            model_name="orcamentofuturo",
            index=models.Index(fields=["data_planejada"], name="financeiro__data_pl_af728f_idx"),
        ),
    ]
