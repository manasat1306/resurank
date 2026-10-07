from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import RecruiterProfile


class RecruiterSignupForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=150)
    company_name = forms.CharField(max_length=150, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if (User.objects.filter(username__iexact=email).exists()
                or User.objects.filter(email__iexact=email).exists()):
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'The two passwords do not match.')
        elif p1:
            try:
                validate_password(p1)
            except forms.ValidationError as error:
                self.add_error('password1', error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        parts = data['full_name'].strip().split(None, 1)
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password1'],
            first_name=parts[0] if parts else '',
            last_name=parts[1] if len(parts) > 1 else '',
        )
        RecruiterProfile.objects.create(
            user=user,
            company_name=data['company_name'].strip(),
        )
        return user