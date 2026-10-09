from django import forms


class ProfileForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    company_name = forms.CharField(max_length=150, required=False)