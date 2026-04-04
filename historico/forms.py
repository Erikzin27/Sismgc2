from django import forms
from .models import HistoricoEvento


class HistoricoForm(forms.ModelForm):
    class Meta:
        model = HistoricoEvento
        fields = ["entidade", "referencia_id", "descricao", "usuario"]
