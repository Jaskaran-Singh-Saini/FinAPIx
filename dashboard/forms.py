# dashboard/forms.py
from django import forms

class StockFilterForm(forms.Form):
    symbol = forms.CharField(required=False, label='Symbol')
    date = forms.DateField(required=False, label='Date', widget=forms.DateInput(attrs={'type': 'date'}))
