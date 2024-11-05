from django import forms
from .models import Provider, LCVTerm  # Import Neo4j models directly
#from .models import LastGeneratedUID

#class LastGeneratedUIDForm(forms.ModelForm):
 #   class Meta:
  #      model = LastGeneratedUID
   #     fields = ['uid']

class ProviderForm(forms.ModelForm):
    # uid = forms.CharField(max_length=255)
    name = forms.CharField(max_length=255)

    def save(self):
        name = self.cleaned_data['name']
        provider = Provider.create_provider(name)
        provider.save()
        return provider

    class Meta:
        model = Provider
        #fields = ['uid', 'name', 'echelon_level']
        fields = ['name'] # UID is self generated

class LCVTermForm(forms.ModelForm):
    provider_name = forms.CharField(max_length=255)
    term = forms.CharField(max_length=255)
    echelon = forms.CharField(max_length=255)
    structure = forms.CharField(max_length=255)

    def save(self):
        payload = self.cleaned_data
        lcv_term = LCVTerm.create_term(provider_name=payload["provider_name"], term=payload['term'], echelon_level=payload["echelon"], structure=payload["structure"])
        lcv_term.save()
        return lcv_term
    class Meta:
        model = LCVTerm
        #fields = ['uid', 'term', 'echelon_level']
        fields = ['provider_name', 'term', 'echelon', 'structure'] # UID is self Generated
