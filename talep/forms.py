from django import forms
from .models import AracTalep

class BaskanlikForm(forms.Form):
    BASKANLIK_SECENEKLERI = [('', 'Başkanlık Seçiniz')] + list(AracTalep.BASKANLIK_SECENEKLERI)

    baskanlik = forms.ChoiceField(
        choices=BASKANLIK_SECENEKLERI,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
