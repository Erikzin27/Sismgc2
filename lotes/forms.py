from django import forms
from .models import Lote


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = [
            "nome",
            "codigo",
            "data_criacao",
            "finalidade",
            "reprodutivo",
            "quantidade_machos",
            "quantidade_femeas",
            "data_inicio_reproducao",
            "status_reprodutivo",
            "observacoes_reproducao",
            "linhagem_principal",
            "quantidade_inicial",
            "quantidade_atual",
            "status",
            "local",
            "observacoes",
            "custo_acumulado",
            "consumo_acumulado",
            "ativo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].help_text = "Código único do lote."
        self.fields["quantidade_inicial"].help_text = "Qtd no início do lote."
        self.fields["quantidade_atual"].help_text = "Opcional. Será preenchido automaticamente."
        self.fields["quantidade_atual"].required = False
        self.fields["reprodutivo"].help_text = "Marque quando o lote for usado para reprodução."
        self.fields["quantidade_machos"].required = False
        self.fields["quantidade_femeas"].required = False
        self.fields["data_inicio_reproducao"].required = False
        self.fields["status_reprodutivo"].required = False
        self.fields["observacoes_reproducao"].required = False
        self.fields["quantidade_machos"].help_text = "Usado apenas para lotes reprodutivos."
        self.fields["quantidade_femeas"].help_text = "Usado apenas para lotes reprodutivos."
        self.fields["data_inicio_reproducao"].help_text = "Data em que o lote entrou em reprodução."
        self.fields["status_reprodutivo"].help_text = "Status operacional da reprodução."
        if "linhagem_principal" in self.fields:
            self.fields["linhagem_principal"].required = False
            self.fields["linhagem_principal"].help_text = "Opcional. Pode ser informado depois."

    def clean(self):
        cleaned = super().clean()
        reprodutivo = cleaned.get("reprodutivo")
        machos = cleaned.get("quantidade_machos") or 0
        femeas = cleaned.get("quantidade_femeas") or 0
        status_reprodutivo = cleaned.get("status_reprodutivo")
        data_inicio_reproducao = cleaned.get("data_inicio_reproducao")
        finalidade = cleaned.get("finalidade")

        if not reprodutivo:
            cleaned["quantidade_machos"] = 0
            cleaned["quantidade_femeas"] = 0
            cleaned["data_inicio_reproducao"] = None
            cleaned["status_reprodutivo"] = ""
            cleaned["observacoes_reproducao"] = ""
            return cleaned

        if finalidade != "reproducao":
            self.add_error("finalidade", "Para usar dados reprodutivos, a finalidade do lote deve ser Reprodução.")
        if machos < 0:
            self.add_error("quantidade_machos", "Quantidade de machos não pode ser negativa.")
        if femeas < 0:
            self.add_error("quantidade_femeas", "Quantidade de fêmeas não pode ser negativa.")
        if machos == 0 and femeas == 0:
            self.add_error("quantidade_femeas", "Informe ao menos uma quantidade reprodutiva.")
        if status_reprodutivo and not data_inicio_reproducao:
            self.add_error("data_inicio_reproducao", "Informe a data de início quando houver status reprodutivo.")
        return cleaned
