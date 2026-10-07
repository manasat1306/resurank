from django import forms

from .models import Job

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB


class AnalyzeResumeForm(forms.Form):
    job = forms.ModelChoiceField(queryset=Job.objects.none(), empty_label='Select a job')
    candidate_name = forms.CharField(max_length=255)
    candidate_email = forms.EmailField(required=False)
    resume_file = forms.FileField()

    def __init__(self, *args, recruiter=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Only this recruiter's own jobs can be chosen
        self.fields['job'].queryset = Job.objects.filter(recruiter=recruiter).order_by('-created_at')

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