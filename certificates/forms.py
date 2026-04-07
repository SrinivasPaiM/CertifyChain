from django import forms

class IssueCertificateForm(forms.Form):
    recipient_address = forms.CharField(label='Recipient Address', max_length=100)
    certificate_data = forms.CharField(label='Certificate Data', widget=forms.Textarea)
    valid_until = forms.DateField(label='Valid Until', widget=forms.DateInput(attrs={'type': 'date'}))
    issuing_date = forms.DateField(label='Issuing Date', widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(label='Address', max_length=255)
    refugee_name = forms.CharField(label='Refugee Name', max_length=100)
    date_of_birth = forms.DateField(label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))
    country = forms.CharField(label='Country', max_length=100)
    gender = forms.ChoiceField(label='Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
