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
        #fields = ['uid', 'name', 'echelon_level']
        fields = ['name', 'echelon_level'] # UID is self generated

class LCVTermForm(forms.ModelForm):
    uid = forms.CharField(max_length=255)
    term = forms.CharField(max_length=255)

    def save(self):
        lcv_term = LCVTerm(uid=self.cleaned_data['uid'], term=self.cleaned_data['term'])
        lcv_term.save()
        return lcv_term
    class Meta:
        model = LCVTerm
        #fields = ['uid', 'term', 'echelon_level']
        fields = ['term', 'echelon_level'] # UID is self Generated
        
# Search Forms
class SearchForm(forms.Form):
    search_term = forms.CharField(max_length=255, required=True, label="Search Term")
    search_type = forms.ChoiceField(choices=[
        ('general', 'General Search'),
        ('alias', 'Search by Alias'),
        ('definition', 'Search by Definition'),
        ('context', 'Search by Context'),
    ], required=True, label="Search Type"
    )
    context = forms.CharField(label='Context', required=False, max_length=255)
