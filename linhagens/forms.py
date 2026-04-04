from django import forms
from .models import Linhagem


class LinhagemForm(forms.ModelForm):
    class Meta:
        model = Linhagem
        fields = ["nome", "descricao", "origem", "observacoes", "ativo"]
