from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Enter your username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter your email address",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Password placeholders (THIS is the key)
        self.fields["password1"].widget.attrs["placeholder"] = "Enter password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("username", css_class="mb-4"),
            Field("email", css_class="mb-4"),
            Field(
                "password1",
                css_class="mb-4",
            ),
            Field("password2", css_class="mb-4"),
            Submit("submit", "Sign Up", css_class="w-full"),
        )


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["placeholder"] = "Enter your email address"
        self.fields["password"].widget.attrs["placeholder"] = "Enter your password"

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("username", css_class="mb-4"),
            Field("password", css_class="mb-4"),
            Submit("submit", "Login In", css_class="w-full"),
        )
