from django import forms
from decimal import Decimal, InvalidOperation
from .models import LancamentoFinanceiro, OrcamentoFuturo


class LancamentoFinanceiroForm(forms.ModelForm):
    FORMA_PAGAMENTO_CHOICES = [
        ("", "Selecione"),
        ("pix", "Pix"),
        ("credito", "Cartão de crédito"),
        ("debito", "Cartão de débito"),
        ("dinheiro", "Dinheiro"),
        ("transferencia", "Transferência"),
        ("boleto", "Boleto"),
        ("outro", "Outro / Manual"),
    ]

    forma_pagamento = forms.ChoiceField(
        choices=FORMA_PAGAMENTO_CHOICES,
        required=False,
    )
    forma_pagamento_outro = forms.CharField(
        required=False,
        label="Forma de pagamento manual",
    )

    class Meta:
        model = LancamentoFinanceiro
        fields = [
            "data",
            "tipo",
            "categoria",
            "descricao",
            "valor",
            "lote",
            "ave",
            "forma_pagamento",
            "observacoes",
            "comprovante",
        ]

    @classmethod
    def _forma_pagamento_code(cls, value):
        normalized = (value or "").strip().lower()
        if not normalized:
            return ""
        for code, label in cls.FORMA_PAGAMENTO_CHOICES:
            if normalized in {code.lower(), label.lower()}:
                return code
        return "outro"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["descricao"].help_text = "Ex: compra de ração, manutenção, venda."
        self.fields["valor"].help_text = "Valor em reais."
        self.fields["forma_pagamento"].help_text = "Selecione a forma principal usada no lançamento."
        self.fields["forma_pagamento_outro"].help_text = "Preencha apenas se selecionar Outro / Manual."
        self.fields["valor"].widget = forms.TextInput(
            attrs={"inputmode": "decimal", "placeholder": "Ex: 1200,50"}
        )
        self.fields["forma_pagamento_outro"].widget = forms.TextInput(
            attrs={"placeholder": "Ex: Cheque, crédito interno, vale"}
        )
        valor_atual = getattr(self.instance, "forma_pagamento", "") or ""
        code = self._forma_pagamento_code(valor_atual)
        self.fields["forma_pagamento"].initial = code
        if valor_atual and code == "outro":
            self.fields["forma_pagamento_outro"].initial = valor_atual
        self.order_fields(
            [
                "data",
                "tipo",
                "categoria",
                "descricao",
                "valor",
                "lote",
                "ave",
                "forma_pagamento",
                "forma_pagamento_outro",
                "observacoes",
                "comprovante",
            ]
        )

    def clean(self):
        cleaned = super().clean()
        if (cleaned.get("valor") is not None) and cleaned.get("valor") < 0:
            self.add_error("valor", "Valor não pode ser negativo.")
        forma_pagamento = cleaned.get("forma_pagamento") or ""
        forma_pagamento_outro = (cleaned.get("forma_pagamento_outro") or "").strip()
        if forma_pagamento == "outro" and not forma_pagamento_outro:
            self.add_error("forma_pagamento_outro", "Informe a forma de pagamento manual.")
        return cleaned

    def clean_valor(self):
        valor = self.data.get("valor")
        if valor is None:
            return None
        if isinstance(valor, str):
            valor = valor.strip()
            if "," in valor and "." in valor:
                valor = valor.replace(".", "").replace(",", ".")
            elif "," in valor:
                valor = valor.replace(",", ".")
        try:
            return Decimal(valor)
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("Valor inválido. Use número, ex: 1200,50")

    def save(self, commit=True):
        instance = super().save(commit=False)
        forma_pagamento = self.cleaned_data.get("forma_pagamento") or ""
        forma_pagamento_outro = (self.cleaned_data.get("forma_pagamento_outro") or "").strip()
        labels = {code: label for code, label in self.FORMA_PAGAMENTO_CHOICES}
        if forma_pagamento == "outro":
            instance.forma_pagamento = forma_pagamento_outro
        else:
            instance.forma_pagamento = labels.get(forma_pagamento, "")
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class OrcamentoFuturoForm(forms.ModelForm):
    class Meta:
        model = OrcamentoFuturo
        fields = [
            "titulo",
            "descricao",
            "categoria",
            "valor_previsto",
            "valor_ja_reservado",
            "status",
            "prioridade",
            "data_planejada",
            "observacoes",
            "foto",
            "ativo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["titulo"].help_text = "Nome do investimento ou compra futura."
        self.fields["categoria"].help_text = "Opcional. Ex: estrutura, equipamento, reforma."
        self.fields["valor_previsto"].help_text = "Valor total estimado para este planejamento."
        self.fields["valor_ja_reservado"].help_text = "Opcional. Valor reservado apenas para acompanhamento interno."
        self.fields["descricao"].required = False
        self.fields["categoria"].required = False
        self.fields["valor_ja_reservado"].required = False
        self.fields["data_planejada"].required = False
        self.fields["observacoes"].required = False
        self.fields["foto"].required = False
        self.fields["valor_previsto"].widget = forms.TextInput(
            attrs={"inputmode": "decimal", "placeholder": "Ex: 15000,00"}
        )
        self.fields["valor_ja_reservado"].widget = forms.TextInput(
            attrs={"inputmode": "decimal", "placeholder": "Ex: 3000,00"}
        )

    def _parse_decimal(self, raw_value):
        if raw_value in (None, ""):
            return None
        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
            if "," in raw_value and "." in raw_value:
                raw_value = raw_value.replace(".", "").replace(",", ".")
            elif "," in raw_value:
                raw_value = raw_value.replace(",", ".")
        try:
            return Decimal(raw_value)
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("Valor inválido. Use número, ex: 1200,50")

    def clean_valor_previsto(self):
        valor = self._parse_decimal(self.data.get("valor_previsto"))
        if valor is None:
            return None
        if valor < 0:
            raise forms.ValidationError("Valor previsto não pode ser negativo.")
        return valor

    def clean_valor_ja_reservado(self):
        valor = self._parse_decimal(self.data.get("valor_ja_reservado"))
        if valor is None:
            return Decimal("0")
        if valor < 0:
            raise forms.ValidationError("Valor já reservado não pode ser negativo.")
        return valor
