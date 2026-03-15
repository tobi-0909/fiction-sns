from django import forms

from .models import World


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = ('title', 'description')
        labels = {
            'title': 'タイトル',
            'description': '説明',
        }
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 120}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
