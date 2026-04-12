from django import forms
from decimal import Decimal
from .models import Reprodutor, Casal
from aves.models import Ave


class ReprodutorForm(forms.ModelForm):
    valor_estimado = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "Ex: 500,00"})
    )

    class Meta:
        model = Reprodutor
        fields = [
            "ave",
            "tipo",
            "status",
            "qualidade_genetica",
            "valor_estimado",
            "data_inicio_reproducao",
            "data_fim_reproducao",
            "observacoes",
        ]
        widgets = {
            "ave": forms.Select(attrs={"class": "form-select"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "qualidade_genetica": forms.Select(attrs={"class": "form-select"}),
            "data_inicio_reproducao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_fim_reproducao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas aves que não têm reprodutor cadastrado ou é o atual
        if self.instance.pk:
            self.fields["ave"].queryset = Ave.objects.filter(
                finalidade=Ave.FINALIDADE_REPRODUCAO
            ) | Ave.objects.filter(reprodutor__pk=self.instance.pk)
        else:
            self.fields["ave"].queryset = Ave.objects.filter(
                finalidade=Ave.FINALIDADE_REPRODUCAO
            ).exclude(reprodutor__isnull=False)

    def clean_valor_estimado(self):
        valor = self.cleaned_data.get("valor_estimado", "").strip()
        if not valor:
            return None
        try:
            valor = Decimal(valor.replace(",", "."))
            if valor < 0:
                raise forms.ValidationError("Valor não pode ser negativo")
            return valor
        except:
            raise forms.ValidationError("Valor inválido")

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        ave = cleaned.get("ave")
        
        if ave and tipo:
            if tipo == Reprodutor.TIPO_MATRIZ and ave.sexo != Ave.SEXO_FEMEA:
                self.add_error("tipo", "Matriz deve ser uma ave fêmea")
            elif tipo == Reprodutor.TIPO_REPRODUTOR and ave.sexo != Ave.SEXO_MACHO:
                self.add_error("tipo", "Reprodutor deve ser uma ave macho")
        
        return cleaned


class CasalForm(forms.ModelForm):
    class Meta:
        model = Casal
        fields = [
            "reprodutor_macho",
            "matriz_femea",
            "lote",
            "data_inicio",
            "data_fim",
            "status",
            "observacoes",
        ]
        widgets = {
            "reprodutor_macho": forms.Select(attrs={"class": "form-select"}),
            "matriz_femea": forms.Select(attrs={"class": "form-select"}),
            "lote": forms.Select(attrs={"class": "form-select"}),
            "data_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_fim": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reprodutor_macho"].queryset = Reprodutor.objects.filter(
            tipo=Reprodutor.TIPO_REPRODUTOR,
            ativo=True
        ).select_related("ave")
        self.fields["reprodutor_macho"].label_from_instance = lambda obj: f"{obj.ave.codigo_interno} - {obj.ave.nome or 'Sem nome'}"
        
        self.fields["matriz_femea"].queryset = Reprodutor.objects.filter(
            tipo=Reprodutor.TIPO_MATRIZ,
            ativo=True
        ).select_related("ave")
        self.fields["matriz_femea"].label_from_instance = lambda obj: f"{obj.ave.codigo_interno} - {obj.ave.nome or 'Sem nome'}"

    def clean(self):
        cleaned = super().clean()
        macho = cleaned.get("reprodutor_macho")
        femea = cleaned.get("matriz_femea")
        
        if macho and femea:
            if macho.ave == femea.ave:
                self.add_error(None, "Reprodutor e matriz devem ser aves diferentes")
        
        return cleaned
