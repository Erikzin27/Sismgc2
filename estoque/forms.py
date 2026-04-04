from django import forms
from .models import ItemEstoque, MovimentoEstoque


class ItemEstoqueForm(forms.ModelForm):
    class Meta:
        model = ItemEstoque
        fields = [
            "nome",
            "categoria",
            "unidade",
            "quantidade_atual",
            "estoque_minimo",
            "custo_unitario",
            "custo_medio",
            "ultimo_preco",
            "validade",
            "fornecedor",
            "localizacao",
            "observacoes",
            "anexo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "ultimo_preco" in self.fields:
            self.fields["ultimo_preco"].disabled = True
            self.fields["ultimo_preco"].help_text = "Último preço pago (automático)."
        if "custo_medio" in self.fields:
            self.fields["custo_medio"].disabled = True
            self.fields["custo_medio"].help_text = "Custo médio calculado automaticamente."


class MovimentoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentoEstoque
        fields = [
            "item",
            "data",
            "tipo",
            "motivo",
            "quantidade",
            "custo_unitario",
            "lote_relacionado",
            "fornecedor",
            "observacoes",
            "anexo",
        ]

    def clean(self):
        cleaned = super().clean()
        has_error = False
        if (cleaned.get("quantidade") is not None) and cleaned.get("quantidade") < 0:
            self.add_error("quantidade", "Quantidade não pode ser negativa.")
            has_error = True
        if (cleaned.get("custo_unitario") is not None) and cleaned.get("custo_unitario") < 0:
            self.add_error("custo_unitario", "Custo unitário não pode ser negativo.")
            has_error = True
        item = cleaned.get("item")
        quantidade = cleaned.get("quantidade")
        tipo = cleaned.get("tipo")
        if item and quantidade and tipo == "saida":
            if item.quantidade_atual < quantidade:
                self.add_error("quantidade", "Quantidade de saída não pode ser maior que o saldo em estoque.")
                has_error = True
        if has_error:
            return cleaned
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["motivo"].help_text = "Motivo da movimentação."
        self.fields["custo_unitario"].help_text = "Preço unitário (em caso de compra)."
