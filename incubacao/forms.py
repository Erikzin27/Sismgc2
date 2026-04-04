from django import forms
from .models import Incubacao


class IncubacaoForm(forms.ModelForm):
    class Meta:
        model = Incubacao
        fields = [
            "codigo",
            "data_entrada",
            "tipo",
            "quantidade_ovos",
            "origem_ovos",
            "matriz_responsavel",
            "lote_relacionado",
            "previsao_eclosao",
            "data_eclosao",
            "quantidade_nascida",
            "ovos_fertis",
            "ovos_infertis",
            "perdas",
            "status",
            "observacoes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].help_text = "Código único da incubação."
        self.fields["quantidade_ovos"].help_text = "Quantidade total de ovos."
        self.fields["previsao_eclosao"].help_text = "Opcional. Calculado automaticamente em 21 dias."
        optional_fields = [
            "origem_ovos",
            "matriz_responsavel",
            "lote_relacionado",
            "previsao_eclosao",
            "data_eclosao",
            "quantidade_nascida",
            "ovos_fertis",
            "ovos_infertis",
            "perdas",
            "observacoes",
        ]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False

    def clean(self):
        cleaned = super().clean()
        entrada = cleaned.get("data_entrada")
        eclosao = cleaned.get("data_eclosao")
        if eclosao and entrada and eclosao < entrada:
            self.add_error("data_eclosao", "A data de eclosão não pode ser anterior à data de entrada.")
        if (cleaned.get("quantidade_ovos") is not None) and cleaned.get("quantidade_ovos") < 0:
            self.add_error("quantidade_ovos", "Quantidade de ovos não pode ser negativa.")
        return cleaned
