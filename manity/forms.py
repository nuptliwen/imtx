from django.forms import ModelForm, TextInput
from manity.models import Purchaser

class PurchaserForm(ModelForm):
    class Meta:
        model = Purchaser
        widgets = {
            'name': TextInput(attrs={'size': 30}),
            'email': TextInput(attrs={'size': 30}),
        }
        exclude =  ('purchased',)
