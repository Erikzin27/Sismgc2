from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("historico", "0003_historicoevento_acao_historicoevento_detalhes"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="historicoevento",
            index=models.Index(fields=["entidade", "referencia_id", "created_at"], name="historico_h_entidad_1995bc_idx"),
        ),
        migrations.AddIndex(
            model_name="historicoevento",
            index=models.Index(fields=["entidade", "acao", "created_at"], name="historico_h_entidad_b31347_idx"),
        ),
        migrations.AddIndex(
            model_name="historicoevento",
            index=models.Index(fields=["usuario", "created_at"], name="historico_h_usuario_69b459_idx"),
        ),
    ]
