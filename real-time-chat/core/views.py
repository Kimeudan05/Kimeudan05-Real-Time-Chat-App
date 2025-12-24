from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "core/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Account created successfully ! Please login now"
        )
        return response


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = "core/login.html"

    def get_success_url(self):
        # update the user status to online
        self.request.user.is_online = True
        self.request.user.save()
        return reverse_lazy("profile")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # update the user status to offline
        if request.user.is_authenticated:
            request.user.is_online = False
            request.user.save()
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        messages.info(self.request, "You have been logged out")
        return reverse_lazy("login")


@login_required
def profile_view(request):
    return render(request, "core/profile.html")
