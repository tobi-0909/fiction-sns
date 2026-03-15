from django import forms

from .models import Character, World


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


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'profile', 'personality')
        labels = {
            'name': '名前',
            'profile': 'プロフィール',
            'personality': '性格・口調メモ',
        }
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 120}),
            'profile': forms.Textarea(attrs={'rows': 4}),
            'personality': forms.Textarea(attrs={'rows': 4}),
        }
