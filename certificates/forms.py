from django import forms

class IssueCertificateForm(forms.Form):
    transaction_hash = forms.CharField(
        label='Transaction Hash', 
        max_length=100, 
        required=True,
        help_text='The transaction hash from Remix/Ganache after deploying the certificate'
    )
    recipient_address = forms.CharField(label='Recipient Ethereum Address', max_length=100)
    certificate_data = forms.CharField(label='Certificate Data', widget=forms.Textarea, required=False)
    valid_until = forms.DateField(label='Valid Until', widget=forms.DateInput(attrs={'type': 'date'}))
    issuing_date = forms.DateField(label='Issuing Date', widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(label='Current Address', max_length=255)
    refugee_name = forms.CharField(label='Refugee Name', max_length=100)
    date_of_birth = forms.DateField(label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))
    country = forms.CharField(label='Country of Origin', max_length=100)
    gender = forms.ChoiceField(label='Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    
    # Extended fields for AI matching
    skills = forms.CharField(label='Skills (comma-separated)', max_length=255, required=False, 
                             help_text='e.g., cooking, driving, computers, languages')
    employment_status = forms.ChoiceField(label='Employment Status', 
        choices=[
            ('', 'Select Status'),
            ('unemployed', 'Unemployed'),
            ('employed', 'Employed'),
            ('self_employed', 'Self-Employed'),
            ('student', 'Student'),
        ],
        required=False
    )
    family_size = forms.IntegerField(label='Family Size', min_value=1, initial=1, required=False)
    has_children = forms.BooleanField(label='Has Children', required=False, initial=False)
    language_proficiency = forms.ChoiceField(label='Language Proficiency (Local Language)',
        choices=[
            (1, 'None/Basic'),
            (2, 'Elementary'),
            (3, 'Intermediate'),
            (4, 'Advanced'),
            (5, 'Fluent'),
        ],
        required=False,
        initial=1
    )
    time_since_arrival = forms.IntegerField(label='Months Since Arrival', min_value=1, initial=1, required=False,
                                             help_text='How many months ago did you arrive in this country?')
    special_needs = forms.BooleanField(label='Special Needs', required=False, initial=False)
