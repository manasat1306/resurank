from django import forms
from resume_analyzer.models import Application

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB


class ApplyForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'candidate_name',
            'candidate_email',
            'candidate_phone',
            'resume_file',
            'consent_given',
        ]

    def __init__(self, *args, job=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        self.fields['consent_given'].required = True
        self.fields['consent_given'].error_messages['required'] = (
            'Please agree to continue.'
        )

    def clean_candidate_email(self):
        email = self.cleaned_data['candidate_email'].strip().lower()
        if self.job and Application.objects.filter(
            job=self.job, candidate_email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "You've already applied to this job."
            )
        return email

    def clean_resume_file(self):
        resume = self.cleaned_data['resume_file']
        if not resume.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Please upload a PDF file.')
        if resume.size > MAX_RESUME_SIZE:
            raise forms.ValidationError('File is too large. Maximum size is 5 MB.')
        if resume.read(5) != b'%PDF-':
            raise forms.ValidationError('This file does not look like a real PDF.')
        resume.seek(0)
        return resume