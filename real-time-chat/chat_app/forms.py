# chat_app/forms.py
from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div
from .models import ChatRoom, Message

User = get_user_model()


class ChatRoomForm(forms.ModelForm):
    """A form for creating a chat room"""

    class Meta:
        model = ChatRoom
        fields = ["name", "description", "room_type"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Enter room description...",
                    "class": "resize-none",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("name", css_class="mb-4"),
            Field("description", css_class="mb-4"),
            Field("room_type", css_class="mb-4"),
            Submit(
                "submit",
                "Create Room",
                css_class="w-full bg-indigo-600 hover:bg-indigo-700",
            ),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
            # Add creator as participant
            instance.participants.add(self.user)
        return instance


class MessageForm(forms.ModelForm):
    """A form for sending a message"""

    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 1,
                    "placeholder": "Type your message...",
                    "class": "resize-none",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_show_labels = False


class DirectMessageForm(forms.Form):
    """A form for sending a direct message from a user to another user"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Enter username to message"}),
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("username", css_class="mb-4"),
            Submit("submit", "Start Chat", css_class="w-full"),
        )

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            user = User.objects.get(username=username)
            if user == self.request_user:
                raise forms.ValidationError("You cannot message yourself")
            return user
        except User.DoesNotExist:
            raise forms.ValidationError("User not found")
