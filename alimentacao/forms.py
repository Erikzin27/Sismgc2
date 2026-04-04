from django import forms
from .models import FormulaRacao


class FormulaRacaoForm(forms.ModelForm):
    class Meta:
        model = FormulaRacao
        fields = ["nome", "fase", "ingredientes", "custo_total", "observacoes"]
