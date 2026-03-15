from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator
from django.utils.crypto import get_random_string


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='メールアドレス', required=True)
    handle = forms.CharField(label='ハンドル名', max_length=30, required=False, help_text='@は不要です（英数字と_のみ、未入力なら自動生成）')
    display_name = forms.CharField(label='表示名', max_length=50, required=False)

    class Meta:
        model = User
        fields = ('email', 'handle', 'display_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('このメールアドレスはすでに使用されています。')
        return email

    def clean_handle(self):
        handle = self.cleaned_data.get('handle', '').strip().lstrip('@').lower()
        if not handle:
            return ''
        if User.objects.filter(handle__iexact=handle).exists():
            raise forms.ValidationError('このハンドル名はすでに使用されています。')
        return handle

    def _generate_unique_handle(self):
        while True:
            candidate = f"user_{get_random_string(8, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')}"
            if not User.objects.filter(handle=candidate).exists():
                return candidate

    def save(self, commit=True):
        user = super().save(commit=False)
        handle = self.cleaned_data['handle'] or self._generate_unique_handle()
        base_username = f'u_{handle}'
        username = base_username
        index = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{index}'
            index += 1

        user.username = username
        user.email = self.cleaned_data['email']
        user.handle = handle
        user.display_name = self.cleaned_data.get('display_name', '').strip() or handle
        if commit:
            user.save()
        return user


class ProfileSettingsForm(forms.ModelForm):
    handle = forms.CharField(
        label='ハンドル名',
        max_length=30,
        validators=[RegexValidator(regex=r'^[A-Za-z0-9_]+$', message='handleは英数字とアンダースコアのみ使用できます。')],
        help_text='@は不要です。英数字と_のみ利用できます。',
    )
    display_name = forms.CharField(label='表示名', max_length=50, required=False)

    class Meta:
        model = User
        fields = ('handle', 'display_name')

    def clean_handle(self):
        handle = self.cleaned_data['handle'].strip().lstrip('@').lower()
        if len(handle) < 3:
            raise forms.ValidationError('handleは3文字以上で入力してください。')
        if len(handle) > 20:
            raise forms.ValidationError('handleは20文字以下で入力してください。')

        exists = User.objects.filter(handle__iexact=handle).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError('このハンドル名はすでに使用されています。')
        return handle

    def save(self, commit=True):
        user = super().save(commit=False)
        user.display_name = self.cleaned_data.get('display_name', '').strip() or user.handle
        if commit:
            user.save()
        return user


class EmailOrHandleAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='メールアドレスまたは@handle', max_length=254)

    def clean(self):
        identifier = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if identifier is not None and password:
            resolved_username = self._resolve_username(identifier)
            self.user_cache = authenticate(self.request, username=resolved_username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def _resolve_username(self, identifier):
        normalized = identifier.strip()
        if normalized.startswith('@'):
            normalized = normalized[1:]

        user = User.objects.filter(email__iexact=normalized).first()
        if user:
            return user.username

        user = User.objects.filter(handle__iexact=normalized).first()
        if user:
            return user.username

        return normalized
