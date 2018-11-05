from django import forms
from django.forms import TextInput

class SentenceForm(forms.Form):
    input_sentence = forms.CharField(widget=forms.TextInput(attrs={'class':'input', 'placeholder' : 'Write your sentence','name':'sentence'}))
