from django import forms
from .models import Vacina, Medicamento, AplicacaoVacina, Tratamento


class VacinaLoteGerarForm(forms.Form):
    data_nascimento = forms.DateField(required=True, label="Data de nascimento do lote")


class VacinaForm(forms.ModelForm):
    class Meta:
        model = Vacina
        fields = ["nome", "fabricante", "dose_recomendada", "carencia_dias", "observacoes", "receita_anexo"]


class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ["nome", "categoria", "validade", "observacoes"]


class AplicacaoVacinaForm(forms.ModelForm):
    class Meta:
        model = AplicacaoVacina
        fields = ["vacina", "ave", "lote", "data_programada", "data_aplicacao", "dose", "status", "observacoes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vacina"].label = "Vacina"
        self.fields["ave"].label = "Ave"
        self.fields["lote"].label = "Lote"
        self.fields["data_programada"].label = "Data prevista"
        self.fields["data_aplicacao"].label = "Data de aplicação"
        self.fields["dose"].label = "Dose aplicada"
        self.fields["status"].label = "Status"
        self.fields["observacoes"].label = "Observações"
        self.fields["data_programada"].help_text = "Data prevista para aplicação."
        optional_fields = ["ave", "lote", "data_aplicacao", "dose", "observacoes"]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False
        self.fields["data_programada"].widget = forms.DateInput(attrs={"type": "date"})
        self.fields["data_aplicacao"].widget = forms.DateInput(attrs={"type": "date"})
        self.fields["observacoes"].widget = forms.Textarea(attrs={"rows": 3})

    def clean(self):
        cleaned = super().clean()
        data_programada = cleaned.get("data_programada")
        data_aplicacao = cleaned.get("data_aplicacao")
        status = cleaned.get("status")
        if data_aplicacao and data_programada and data_aplicacao < data_programada:
            self.add_error("data_aplicacao", "A data de aplicação não pode ser anterior à data programada.") 
        if not cleaned.get("ave") and not cleaned.get("lote"):
            raise forms.ValidationError("Informe uma ave ou um lote para a aplicação da vacina.")
        if status == AplicacaoVacina.STATUS_APLICADA and not data_aplicacao:
            self.add_error("data_aplicacao", "Informe a data de aplicação quando o status for 'Aplicada'.")
        return cleaned


class TratamentoForm(forms.ModelForm):
    class Meta:
        model = Tratamento
        fields = [
            "ave",
            "lote",
            "doenca",
            "medicamento",
            "data_inicio",
            "data_fim",
            "periodo_carencia",
            "observacoes",
            "receita_anexo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["periodo_carencia"].help_text = "Dias de carência após o tratamento."
        optional_fields = ["ave", "lote", "data_fim", "observacoes", "receita_anexo"]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False

    def clean(self):
        cleaned = super().clean()
        data_inicio = cleaned.get("data_inicio")
        data_fim = cleaned.get("data_fim")
        if data_fim and data_inicio and data_fim < data_inicio:
            self.add_error("data_fim", "A data de fim não pode ser anterior à data de início.")
        if cleaned.get("periodo_carencia") is not None and cleaned.get("periodo_carencia") < 0:
            self.add_error("periodo_carencia", "Período de carência não pode ser negativo.")
        if not cleaned.get("ave") and not cleaned.get("lote"):
            raise forms.ValidationError("Informe uma ave ou um lote para o tratamento.")
        return cleaned
