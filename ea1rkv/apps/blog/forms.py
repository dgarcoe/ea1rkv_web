from django import forms
from django.utils.translation import gettext_lazy as _


class CommentForm(forms.Form):
    name = forms.CharField(label=_("Nombre o indicativo"), max_length=100,
                           widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}))
    text = forms.CharField(label=_("Comentario"), max_length=3000,
                           widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    consent = forms.BooleanField(label=_("Acepto que mi nombre o indicativo y mi comentario se publiquen en esta web."))
