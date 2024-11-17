from django import forms
from .models import GeneratedApp, ModelField
from django.forms import modelformset_factory

class GeneratedAppForm(forms.ModelForm):
    class Meta:
        model = GeneratedApp
        fields = ['name']

class ModelFieldForm(forms.ModelForm):
    class Meta:
        model = ModelField
        fields = ['name', 'field_type', 'max_length', 'is_required']

# For handling multiple fields at once
ModelFieldFormSet = modelformset_factory(ModelField, form=ModelFieldForm, extra=1)
