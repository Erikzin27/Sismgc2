from django import forms
from .models import Nascimento


class NascimentoForm(forms.ModelForm):
    class Meta:
        model = Nascimento
        fields = [
            "data",
            "incubacao",
            "quantidade_nascida",
            "quantidade_viva",
            "quantidade_morta",
            "linhagem",
            "lote_destino",
            "observacoes",
        ]

    def clean(self):
        cleaned = super().clean()
        nascida = cleaned.get("quantidade_nascida") or 0
        viva = cleaned.get("quantidade_viva") or 0
        morta = cleaned.get("quantidade_morta") or 0
        if nascida < 0 or viva < 0 or morta < 0:
            raise forms.ValidationError("Quantidades não podem ser negativas.")
        if nascida == 0 and (viva or morta):
            cleaned["quantidade_nascida"] = viva + morta
        if viva > nascida:
            self.add_error("quantidade_viva", "Quantidade viva não pode ser maior que a nascida.")
        if nascida and (viva + morta) > nascida:
            self.add_error("quantidade_morta", "Soma de viva e morta não pode exceder nascida.")
        # Auto-ajuste quando morta não foi informada
        if nascida and viva and morta == 0:
            cleaned["quantidade_morta"] = max(nascida - viva, 0)
        return cleaned
