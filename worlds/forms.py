from django import forms
from django.contrib.auth import get_user_model

from .models import Character, Post, World, WorldMembership, Report


User = get_user_model()


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = ('title', 'description', 'visibility')
        labels = {
            'title': 'タイトル',
            'description': '説明',
            'visibility': '公開範囲',
        }
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 120}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'visibility': forms.Select(),
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


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('character', 'text')
        labels = {
            'character': 'Character',
            'text': '投稿内容',
        }
        widgets = {
            'character': forms.Select(),
            'text': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, world=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Character.objects.none()
        if world is not None and user is not None:
            queryset = Character.objects.filter(world_entries__world=world, owner=user)
        elif world is not None:
            queryset = Character.objects.filter(world=world)
        first_character = queryset.first()
        if first_character and not self.is_bound:
            self.fields['character'].initial = first_character.pk

        self.fields['character'].queryset = queryset


class ModerationActionForm(forms.Form):
    ACTION_KICK = 'kick'
    ACTION_BAN = 'ban'

    target_handle = forms.CharField(label='対象ユーザー', max_length=30, help_text='@は不要です。')
    action = forms.ChoiceField(
        label='操作',
        choices=((ACTION_KICK, 'kick'), (ACTION_BAN, 'ban')),
    )

    def __init__(self, *args, world=None, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.world = world
        self.actor = actor
        self.target_user = None

    def clean_target_handle(self):
        handle = self.cleaned_data['target_handle'].strip().lstrip('@').lower()
        try:
            self.target_user = User.objects.get(handle__iexact=handle)
        except User.DoesNotExist as exc:
            raise forms.ValidationError('指定されたユーザーが見つかりません。') from exc

        if self.world and self.world.owner_id == self.target_user.id:
            raise forms.ValidationError('World作成者自身は対象にできません。')

        return handle

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        if not action or self.target_user is None or self.world is None:
            return cleaned_data

        membership = WorldMembership.objects.filter(world=self.world, user=self.target_user).first()
        if action == self.ACTION_KICK:
            if membership is None or membership.status != WorldMembership.Status.ACTIVE:
                raise forms.ValidationError('kick は active 状態の参加者にのみ実行できます。')

        return cleaned_data


class ReportForm(forms.ModelForm):
	class Meta:
		model = Report
		fields = ('reason', 'description')
		labels = {
			'reason': '通報理由',
			'description': '詳細（オプション）',
		}
		widgets = {
			'reason': forms.Select(),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': '具体的な内容を入力してください（任意）'}),
		}
