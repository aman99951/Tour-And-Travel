from .models import TourDate
from django import forms
from travel.models import *


class UserProfileForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    agree_terms = forms.BooleanField(required=True)
    over_18 = forms.BooleanField(required=True)

    class Meta:
        model = UserProfile
        fields = [
            'email', 'password', 'confirm_password', 'mobile_number', 'title', 'first_name', 'last_name',
            'address', 'city', 'postal_code', 'country', 'country_of_passport', 'landline_number',
            'company_address', 'company_city', 'company_state', 'company_postal_code', 'company_country',
            'agree_terms', 'over_18'
        ]
        widgets = {
            'password': forms.PasswordInput(),
            'confirm_password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class TourDateAdminForm(forms.ModelForm):
    class Meta:
        model = TourDate
        fields = '__all__'

    class Media:
        js = ('admin/js/tour_date_admin.js',)


class UserProfileForm2(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'address', 'city', 'postal_code', 'country', 'country_of_passport',
            'landline_number', 'company_address', 'company_city',
            'company_state', 'company_postal_code', 'company_country'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'country_of_passport': forms.TextInput(attrs={'class': 'form-control'}),
            'landline_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company_city': forms.TextInput(attrs={'class': 'form-control'}),
            'company_state': forms.TextInput(attrs={'class': 'form-control'}),
            'company_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_country': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'deparment', 'description', 'attachments']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            # Department field
            'deparment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            # Attachments field
            'attachments': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter your message...'}),
        }


class AdvancePaymentForm(forms.ModelForm):
    class Meta:
        model = AdvancePayment
        fields = ['name', 'mobile', 'email',
                  'amount', 'remark', 'payment_method']


class TourDetailAdminForm(forms.ModelForm):
    class Meta:
        model = TourDetail
        fields = '__all__'  # Use all fields
