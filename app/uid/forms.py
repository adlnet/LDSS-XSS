from django import forms
from .models import Provider, LCVTerm  # Import Neo4j models directly
#from .models import LastGeneratedUID

#class LastGeneratedUIDForm(forms.ModelForm):
 #   class Meta:
  #      model = LastGeneratedUID
   #     fields = ['uid']

class ProviderForm(forms.ModelForm):
    uid = forms.CharField(max_length=255)
    name = forms.CharField(max_length=255)

    def save(self):
        provider = Provider(uid=self.cleaned_data['uid'], name=self.cleaned_data['name'])
        provider.save()
        return provider
    class Meta:
        model = Provider
        fields = ['uid', 'name']

class LCVTermForm(forms.ModelForm):
    uid = forms.CharField(max_length=255)
    term = forms.CharField(max_length=255)

    def save(self):
        lcv_term = LCVTerm(uid=self.cleaned_data['uid'], term=self.cleaned_data['term'])
        lcv_term.save()
        return lcv_term
    class Meta:
        model = LCVTerm
        fields = ['uid', 'term']
