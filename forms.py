from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, StudyGroup


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=150)
    last_name = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="Электронная почта")
    phone = forms.CharField(label="Телефон", max_length=20)
    birth_date = forms.DateField(
        label="Дата рождения",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    group = forms.ModelChoiceField(
        label="Учебная группа",
        queryset=StudyGroup.objects.all().order_by("start_date"),
        empty_label="Выберите группу",
    )
    transmission_type = forms.ChoiceField(
        label="Коробка передач",
        choices=Student._meta.get_field("transmission_type").choices,
    )

    class Meta:
        model = User
        fields = (
            "username", "first_name", "last_name", "email",
            "phone", "birth_date", "group", "transmission_type",
            "password1", "password2",
        )
        labels = {"username": "Логин"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                group=self.cleaned_data["group"],
                birth_date=self.cleaned_data["birth_date"],
                phone=self.cleaned_data["phone"],
                transmission_type=self.cleaned_data["transmission_type"],
            )
        return user
