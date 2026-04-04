from django import forms
from .models import RegistroGenetico


class RegistroGeneticoForm(forms.ModelForm):
    class Meta:
        model = RegistroGenetico
        fields = ["pai", "mae", "filho", "observacoes"]

    consanguinidade_alerta = ""

    def clean(self):
        cleaned = super().clean()
        pai = cleaned.get("pai")
        mae = cleaned.get("mae")
        filho = cleaned.get("filho")

        if pai and mae and pai == mae:
            self.consanguinidade_alerta = "Atenção: pai e mãe informados são a mesma ave."
        elif pai and mae:
            if pai in {mae.pai, mae.mae} or mae in {pai.pai, pai.mae}:
                self.consanguinidade_alerta = "Atenção: existe parentesco direto básico entre pai e mãe."
            elif pai.pai and mae.pai and pai.pai == mae.pai:
                self.consanguinidade_alerta = "Atenção: pai e mãe compartilham o mesmo pai."
            elif pai.mae and mae.mae and pai.mae == mae.mae:
                self.consanguinidade_alerta = "Atenção: pai e mãe compartilham a mesma mãe."

        if filho and pai and filho == pai:
            self.add_error("filho", "O filho não pode ser o mesmo registro do pai.")
        if filho and mae and filho == mae:
            self.add_error("filho", "O filho não pode ser o mesmo registro da mãe.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        filho = instance.filho
        if filho:
            if instance.pai:
                filho.pai = instance.pai
            if instance.mae:
                filho.mae = instance.mae
            if commit:
                filho.save()
        if commit:
            instance.save()
            self.save_m2m()
        return instance
