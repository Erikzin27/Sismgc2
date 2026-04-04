from django import forms
from .models import Abate


class AbateForm(forms.ModelForm):
    class Meta:
        model = Abate
        fields = [
            "data",
            "lote",
            "aves",
            "quantidade_abatida",
            "peso_total",
            "peso_medio",
            "custo_acumulado",
            "receita_gerada",
            "destino",
            "observacoes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = ["lote", "aves", "peso_medio", "destino", "observacoes"]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False

    def clean(self):
        cleaned = super().clean()
        has_error = False
        if (cleaned.get("quantidade_abatida") is not None) and cleaned.get("quantidade_abatida") < 0:
            self.add_error("quantidade_abatida", "Quantidade abatida não pode ser negativa.")
            has_error = True
        if (cleaned.get("peso_total") is not None) and cleaned.get("peso_total") < 0:
            self.add_error("peso_total", "Peso total não pode ser negativo.")
            has_error = True
        if (cleaned.get("custo_acumulado") is not None) and cleaned.get("custo_acumulado") < 0:
            self.add_error("custo_acumulado", "Custo acumulado não pode ser negativo.")
            has_error = True
        if (cleaned.get("receita_gerada") is not None) and cleaned.get("receita_gerada") < 0:
            self.add_error("receita_gerada", "Receita gerada não pode ser negativa.")
            has_error = True
        if not cleaned.get("lote") and not cleaned.get("aves"):
            raise forms.ValidationError("Informe um lote ou selecione aves para o abate.")
        if has_error:
            return cleaned
        return cleaned
