from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm, EmailOrHandleAuthenticationForm


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
