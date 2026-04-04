from django import forms
from core.models import ConfiguracaoSistema


class ConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema
        fields = [
            "nome_sistema",
            "nome_granja",
            "tema_padrao",
            "logo_ativa",
            "dias_alerta_vencimento",
            "observacoes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome_sistema"].help_text = "Nome exibido no topo do sistema."
        self.fields["nome_granja"].help_text = "Opcional. Identificação da granja/empresa."
        self.fields["tema_padrao"].help_text = "Define o tema padrão para novos acessos."
        self.fields["logo_ativa"].help_text = "Caminho do arquivo de logo em static. Ex: img/logo.png"      
        self.fields["dias_alerta_vencimento"].help_text = "Dias antes do vencimento para considerar item 'vencendo'."
        self.fields["observacoes"].help_text = "Observações internas."
