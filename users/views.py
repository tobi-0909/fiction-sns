from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import (
	CustomUserCreationForm,
	EmailOrHandleAuthenticationForm,
	ProfileSettingsForm,
)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailOrHandleAuthenticationForm


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {'form': form})


@login_required
def dashboard(request):
	return render(request, 'users/dashboard.html')


@login_required
def profile_settings(request):
	if request.method == 'POST':
		form = ProfileSettingsForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			return redirect('dashboard')
	else:
		form = ProfileSettingsForm(instance=request.user)

	return render(request, 'users/profile_settings.html', {'form': form})
