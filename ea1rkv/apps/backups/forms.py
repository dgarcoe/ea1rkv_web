from django import forms


class RestoreBackupForm(forms.Form):
    backup_file = forms.FileField(
        label="Archivo de copia",
        help_text="Selecciona un archivo .ea1rkv creado por esta aplicación.",
    )
    confirmation = forms.CharField(
        label="Confirmación",
        help_text='Escribe exactamente "RESTAURAR" para continuar.',
    )

    def clean_confirmation(self):
        value = self.cleaned_data["confirmation"].strip()
        if value != "RESTAURAR":
            raise forms.ValidationError('Debes escribir exactamente "RESTAURAR".')
        return value
