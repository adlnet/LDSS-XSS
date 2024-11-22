from django import forms
<<<<<<< HEAD
from .models import Provider, LCVTerm, Alias  # Import Neo4j models directly
=======
from .models import Provider, LCVTerm, UIDRequestToken # Import Neo4j models directly
from uuid import uuid4
>>>>>>> 6a601dac0354438e1cedd7a6ac4c2fe85966d438
#from .models import LastGeneratedUID

#class LastGeneratedUIDForm(forms.ModelForm):
 #   class Meta:
  #      model = LastGeneratedUID
   #     fields = ['uid']

# class UIDRequestForm(forms.ModelForm):
#     token = forms.CharField(max_length=255)
#     provider_name = forms.CharField(max_length=255)
#     echelon = forms.CharField(max_length=255)
#     termset = forms.CharField(max_length=255)

#     def save(self):
#         given_provider = self.cleaned_data['provider']
#         given_echelon = self.cleaned_data['echelon']
#         given_termset = self.cleaned_data['termset']

#         provider_already_exists = Provider.does_provider_exist(given_provider)
#         if provider_already_exists:
#             provider = Provider.get_provider_by_name(given_provider)
#         else:
#             provider = Provider.create_provider(given_provider)
        
#         uid_request = UIDRequestToken()
#         uid_request.provider_name = provider.name
#         uid_request.echelon = given_echelon
#         uid_request.termset = given_termset
#         uid_request.token = uuid4()

#         uid_request.save()

#         return uid_request

#     class Meta:
#         model = UIDRequestToken
#         #fields = ['uid', 'name', 'echelon_level']
#         fields = ['provider_name', 'echelon', 'termset', 'token'] # UID is self generated

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
<<<<<<< HEAD
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
    
# Alias with no Context  
#class AliasForm(forms.Form):
 #   alias = forms.CharField(max_length=255)
  #  context = forms.CharField(max_length=255, required=False)  # context is optional

#class AliasForm(forms.ModelForm):
 #   class Meta:
  #      model = Alias
   #     fields = ['alias', 'context']  # Include alias and context fields

#class AliasForm(forms.Form):
 #   alias = forms.CharField(max_length=255, required=True)
  #  context = forms.CharField(max_length=255, required=False)

   # def save(self):
        # Save directly to Neo4j via Neomodel
    #    alias = Alias(alias=self.cleaned_data['alias'], context=self.cleaned_data.get('context'))
     #   alias.save()
      #  return alias
      
class AliasForm(forms.Form):
    alias = forms.CharField(max_length=255, required=True)  # The alias name
    context = forms.CharField(max_length=255, required=False)  # Context as a string (the term's name)

    def save(self):
        # Create and save Alias
        alias = Alias(alias=self.cleaned_data['alias'], context=self.cleaned_data.get('context'))
        alias.save()

        # Optionally, if context is provided, link to the NeoTerm
        if alias.context:
            term = NeoTerm.nodes.get_or_none(name=alias.context)
            if term:
                alias.link_to_term(term)  # Link this alias to the found NeoTerm

        return alias
=======
        fields = ['provider_name', 'term', 'echelon', 'structure'] # UID is self Generated
>>>>>>> 6a601dac0354438e1cedd7a6ac4c2fe85966d438
