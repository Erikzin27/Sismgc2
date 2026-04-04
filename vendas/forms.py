from django import forms
from decimal import Decimal, InvalidOperation
from .models import Venda

TWOPLACES = Decimal("0.01")


class VendaForm(forms.ModelForm):
    quantidade = forms.CharField(
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "Ex: 10 ou 10,5"})
    )
    valor_unitario = forms.CharField(
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "Ex: 12,50"})
    )
    desconto = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "Ex: 0,00"})
    )
    valor_total = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "Ex: 1200,50"})
    )

    class Meta:
        model = Venda
        fields = [
            "data",
            "cliente",
            "produto",
            "categoria",
            "quantidade",
            "unidade",
            "valor_unitario",
            "desconto",
            "valor_total",
            "forma_pagamento",
            "status_pagamento",
            "observacoes",
            "lote",
            "ave",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = ["desconto", "valor_total", "forma_pagamento", "observacoes", "lote", "ave"]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False

    def _to_decimal(self, valor):
        if valor is None:
            return None
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                return None
            if "," in valor and "." in valor:
                valor = valor.replace(".", "").replace(",", ".")
            elif "," in valor:
                valor = valor.replace(",", ".")
        try:
            return Decimal(valor)
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("Valor inválido. Use número, ex: 1200,50")

    def clean(self):
        cleaned = super().clean()
        has_error = False
        cleaned["quantidade"] = self._to_decimal(cleaned.get("quantidade"))
        cleaned["valor_unitario"] = self._to_decimal(cleaned.get("valor_unitario"))
        cleaned["desconto"] = self._to_decimal(cleaned.get("desconto")) or 0
        if cleaned.get("valor_total") not in (None, ""):
            cleaned["valor_total"] = self._to_decimal(cleaned.get("valor_total"))
        else:
            cleaned["valor_total"] = None

        if cleaned.get("quantidade") is None:
            self.add_error("quantidade", "Informe a quantidade.")
            has_error = True
        if cleaned.get("valor_unitario") is None:
            self.add_error("valor_unitario", "Informe o valor unitário.")
            has_error = True
        if (cleaned.get("quantidade") is not None) and cleaned.get("quantidade") < 0:
            self.add_error("quantidade", "Quantidade não pode ser negativa.")
            has_error = True
        if (cleaned.get("valor_unitario") is not None) and cleaned.get("valor_unitario") < 0:
            self.add_error("valor_unitario", "Valor unitário não pode ser negativo.")
            has_error = True
        if (cleaned.get("desconto") is not None) and cleaned.get("desconto") < 0:
            self.add_error("desconto", "Desconto não pode ser negativo.")
            has_error = True
        if not cleaned.get("valor_total"):
            quantidade = cleaned.get("quantidade") or 0
            valor_unitario = cleaned.get("valor_unitario") or 0
            desconto = cleaned.get("desconto") or 0
            cleaned["valor_total"] = ((quantidade * valor_unitario) - desconto).quantize(TWOPLACES)
        elif cleaned.get("valor_total") is not None:
            cleaned["valor_total"] = cleaned["valor_total"].quantize(TWOPLACES)
        if has_error:
            return cleaned
        return cleaned
