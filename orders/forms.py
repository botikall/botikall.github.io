import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Comment, ContactMessage, CustomUser


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "message"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields["name"].initial = user.get_full_name()
            self.fields["email"].initial = user.email
            self.fields["name"].widget.attrs["readonly"] = True
            self.fields["email"].widget.attrs["readonly"] = True
            self.fields["phone"].widget.attrs["readonly"] = True
            self.fields.pop("name")
            self.fields.pop("email")
            self.fields.pop("phone")


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, f"{i}★") for i in range(1, 6)]),
        }


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True, help_text="Введіть ваше ім'я."
    )
    last_name = forms.CharField(
        max_length=30, required=True, help_text="Введіть ваше прізвище."
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        help_text="Введіть ваш номер телефону.",
    )
    email = forms.EmailField(required=True, help_text="Введіть вашу електронну пошту.")
    username = forms.CharField(
        max_length=15,
        required=True,
        help_text="Не більше 15 символів. Лише літери, цифри та @/./+/-/_.",
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password1",
            "password2",
        )

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if not re.match(r"^\+380\d{9}$", phone):
            raise ValidationError("Номер телефону має бути у форматі +380XXXXXXXXX.")
        return phone


class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone_number"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
        return user
