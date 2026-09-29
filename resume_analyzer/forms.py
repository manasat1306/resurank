from django import forms
from .models import Job

INPUT = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400"

EXPERIENCE_CHOICES = [
    ('', 'Select experience level'),
    ('Fresher (0-1 years)', 'Fresher (0-1 years)'),
    ('1-3 years', '1-3 years'),
    ('3-5 years', '3-5 years'),
    ('5+ years', '5+ years'),
]


class JobForm(forms.ModelForm):
    # chips send skills as one comma text, we turn it into a list
    required_skills = forms.CharField(required=False)
    preferred_skills = forms.CharField(required=False)
    experience = forms.ChoiceField(choices=EXPERIENCE_CHOICES, required=False)

    class Meta:
        model = Job
        fields = [
            'title', 'department', 'location', 'experience', 'job_type',
            'description_text', 'required_skills', 'preferred_skills',
            'education', 'skill_weight',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['title', 'department', 'location', 'experience',
                     'job_type', 'description_text', 'education']:
            self.fields[name].widget.attrs['class'] = INPUT
        self.fields['title'].widget.attrs['placeholder'] = 'e.g. Python Backend Developer'
        self.fields['department'].widget.attrs['placeholder'] = 'e.g. Engineering'
        self.fields['location'].widget.attrs['placeholder'] = 'e.g. Bengaluru'
        self.fields['education'].widget.attrs['placeholder'] = "e.g. B.Tech / MCA / Bachelor's degree"
        self.fields['description_text'].widget.attrs.update({
            'rows': 6,
            'placeholder': "Describe the role, responsibilities, and what you're looking for...",
        })

        if self.instance and self.instance.pk:
            self.initial['required_skills'] = ', '.join(self.instance.required_skills)
            self.initial['preferred_skills'] = ', '.join(self.instance.preferred_skills)

    def _split(self, value):
        seen, out = set(), []
        for s in (value or '').split(','):
            s = s.strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                out.append(s)
        return out

    def clean_required_skills(self):
        return self._split(self.cleaned_data.get('required_skills'))

    def clean_preferred_skills(self):
        return self._split(self.cleaned_data.get('preferred_skills'))