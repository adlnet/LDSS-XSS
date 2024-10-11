from django import forms
from .models import Provider, LCVTerm

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name']

class LCVTermForm(forms.ModelForm):
    class Meta:
        model = LCVTerm
        fields = ['term', 'ld_lcv_structure']