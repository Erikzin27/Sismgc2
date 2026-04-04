from decimal import Decimal, InvalidOperation

from django import forms
from .models import Ave


class AveForm(forms.ModelForm):
    class Meta:
        model = Ave
        fields = [
            "codigo_interno",
            "identificacao",
            "nome",
            "sexo",
            "finalidade",
            "data_nascimento",
            "linhagem",
            "pai",
            "mae",
            "origem",
            "lote_atual",
            "peso_atual",
            "valor_referencia",
            "status",
            "observacoes",
            "ativo",
            "foto",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo_interno"].help_text = "Identificador interno obrigatório."
        self.fields["identificacao"].help_text = "Opcional. Ex: anilha, chip, etiqueta."
        self.fields["origem"].help_text = "Opcional. Ex: compra, incubação, doação."
        self.fields["peso_atual"].help_text = "Opcional. Informe em kg."
        self.fields["valor_referencia"].help_text = "Opcional. Valor estimado ou referência da ave."
        self.fields["valor_referencia"].required = False
        self.fields["valor_referencia"].widget = forms.TextInput(
            attrs={"inputmode": "decimal", "placeholder": "Ex: 350,00"}
        )
        if "linhagem" in self.fields:
            self.fields["linhagem"].required = False
            self.fields["linhagem"].help_text = "Opcional. Pode ficar em branco quando a procedência for desconhecida."
        optional_fields = [
            "identificacao",
            "nome",
            "data_nascimento",
            "pai",
            "mae",
            "origem",
            "lote_atual",
            "peso_atual",
            "valor_referencia",
            "observacoes",
            "foto",
        ]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False
        if "pai" in self.fields:
            self.fields["pai"].help_text = "Opcional. Pode ficar em branco se a procedência for desconhecida."
        if "mae" in self.fields:
            self.fields["mae"].help_text = "Opcional. Pode ficar em branco se a procedência for desconhecida."

    def clean_valor_referencia(self):
        valor = self.data.get("valor_referencia")
        if valor in (None, ""):
            return None
        if isinstance(valor, str):
            valor = valor.strip()
            if "," in valor and "." in valor:
                valor = valor.replace(".", "").replace(",", ".")
            elif "," in valor:
                valor = valor.replace(",", ".")
        try:
            valor = Decimal(valor)
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("Valor inválido. Use número, ex: 350,00")
        if valor < 0:
            raise forms.ValidationError("O valor da ave não pode ser negativo.")
        return valor
