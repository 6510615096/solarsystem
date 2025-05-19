from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Role, SolarPlant

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['username']
        user.is_active = False
        
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user
    
class SolarPlantForm(forms.ModelForm):
    class Meta:
        model = SolarPlant
        fields = ['name', 'properties', 'address', 'invited_emails']
        labels = {
            'name': 'Solar Plant Name',
            'properties': 'Solar Plant properties',
            'invited_emails': 'Access control',
            'address': 'Address',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Please type a solar plant name'}),
            'properties': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please type a solar plant properties'}),
            'address': forms.TextInput(attrs={'placeholder': 'Please type an address'}),
            'invited_emails': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Invite people to access this solar plant by their email'}),
        }