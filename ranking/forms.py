from django import forms
from .models import PrivateLeague

class PrivateLeagueForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        required=True,
        min_length=6,
        help_text="Password required (min. 6 characters)",
    )

    password_confirm = forms.CharField(
        label="Confirm Password",
        required=True,
    )

    class Meta:
        model = PrivateLeague
        fields = ['name', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        pwd_conf = cleaned_data.get("password_confirm")
        
        if pwd and pwd_conf and pwd != pwd_conf:
            self.add_error("password_confirm", "Passwords do not match.")

    def save(self, commit=True, creator=None):
        league = super().save(commit=False)

        if creator:
            league.creator = creator

        league.set_password(self.cleaned_data['password'])
        
        if commit:
            league.members.add(creator)
            league.save()

        return league