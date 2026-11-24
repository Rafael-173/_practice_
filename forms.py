from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Instructor, Branch
from .models import Student, StudyGroup, Branch, Instructor
from .models import InstructorSlot
from django import forms
from .models import Car
from django.utils import timezone
from django.core.exceptions import ValidationError

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

class InstructorLoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин инструктора", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class InstructorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=150)
    last_name = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="Электронная почта")
    phone = forms.CharField(label="Телефон", max_length=20)
    branch = forms.ModelChoiceField(
        label="Филиал",
        queryset=Branch.objects.all().order_by("name"),
        empty_label="Выберите филиал",
    )
    experience_years = forms.IntegerField(
        label="Стаж вождения (лет)",
        min_value=0,
        max_value=60,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "branch", "experience_years", "password1", "password2")
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
            Instructor.objects.create(
                user=user,
                branch=self.cleaned_data["branch"],
                experience_years=self.cleaned_data["experience_years"],
            )
        return user
    

class SlotForm(forms.ModelForm):
    class Meta:
        model = InstructorSlot
        fields = ('date', 'start_time', 'end_time')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise ValidationError("Нельзя создать окно на прошедшую дату.")
        return date

class CarPhotoForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ("brand", "model", "plate_number","year", "instructor", "photo")
        labels = {
            "brand": "Марка",
            "model": "Модель",
            "plate_number": "Госномер",
            "year": "Год выпуска",
            "instructor": "Инструктор",
            "photo": "Фото автомобиля",
        }

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Размер изображения не должен превышать 2 МБ.")
            from PIL import Image, UnidentifiedImageError
            try:
                image = Image.open(photo)
                if image.format not in ("JPEG", "PNG"):
                    raise forms.ValidationError("Разрешены только изображения JPEG и PNG.")
                image.verify()
                photo.seek(0)
            except (UnidentifiedImageError, OSError):
                raise forms.ValidationError("Файл не является корректным изображением.")
        return photo