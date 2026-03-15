from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='メールアドレス', required=True)
    handle = forms.CharField(label='ハンドル名', max_length=30, help_text='@は不要です（英数字と_のみ）')
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
        handle = self.cleaned_data['handle'].strip().lstrip('@').lower()
        if not handle:
            raise forms.ValidationError('ハンドル名を入力してください。')
        if User.objects.filter(handle__iexact=handle).exists():
            raise forms.ValidationError('このハンドル名はすでに使用されています。')
        return handle

    def save(self, commit=True):
        user = super().save(commit=False)
        handle = self.cleaned_data['handle']
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
