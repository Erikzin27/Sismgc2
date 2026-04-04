from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendas", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="venda",
            index=models.Index(fields=["status_pagamento", "data"], name="vendas_vend_status__cf9f81_idx"),
        ),
        migrations.AddIndex(
            model_name="venda",
            index=models.Index(fields=["lote", "data"], name="vendas_vend_lote_id_6107c7_idx"),
        ),
        migrations.AddIndex(
            model_name="venda",
            index=models.Index(fields=["categoria", "data"], name="vendas_vend_categor_65684d_idx"),
        ),
    ]
