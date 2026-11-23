from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    code = models.CharField(max_length=2, unique=True, verbose_name="Код категории")
    name = models.CharField(max_length=50, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория ТС"
        verbose_name_plural = "Категории ТС"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название филиала")
    address = models.CharField(max_length=200, verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class StudyGroup(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="groups", verbose_name="Категория")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="groups", verbose_name="Филиал")
    name = models.CharField(max_length=50, verbose_name="Название группы")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Стоимость")
    max_students = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)], verbose_name="Максимум курсантов")

    class Meta:
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "name"], name="unique_group_per_branch"),
            models.CheckConstraint(condition=models.Q(end_date__gt=models.F("start_date")), name="end_after_start"),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.code})"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student", verbose_name="Пользователь")
    group = models.ForeignKey(StudyGroup, on_delete=models.PROTECT, related_name="students", verbose_name="Группа")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    transmission_type = models.CharField(max_length=3, choices=[("MT", "МКПП"), ("AT", "АКПП")], default="MT", verbose_name="Тип КПП")
    contract_hours = models.PositiveIntegerField(default=56, verbose_name="Норма часов по договору")
    license_passed = models.BooleanField(default=False, verbose_name="Права получены")

    class Meta:
        verbose_name = "Курсант"
        verbose_name_plural = "Курсанты"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.group.name}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher", verbose_name="Пользователь")
    specialization = models.CharField(max_length=100, verbose_name="Специализация")

    class Meta:
        verbose_name = "Преподаватель теории"
        verbose_name_plural = "Преподаватели теории"

    def __str__(self):
        return self.user.get_full_name()


class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor", verbose_name="Пользователь")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="instructors", verbose_name="Филиал")
    experience_years = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(60)], verbose_name="Стаж, лет")
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)], verbose_name="Рейтинг")

    class Meta:
        verbose_name = "Инструктор"
        verbose_name_plural = "Инструкторы"
        ordering = ["-rating", "user__last_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.branch.name})"


class InstructorSlot(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="slots", verbose_name="Инструктор")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Начало")
    end_time = models.TimeField(verbose_name="Окончание")
    is_booked = models.BooleanField(default=False, verbose_name="Занято")

    class Meta:
        verbose_name = "Окно инструктора"
        verbose_name_plural = "Окна инструктора"
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(fields=["instructor", "date", "start_time"], name="unique_slot"),
            models.CheckConstraint(condition=models.Q(end_time__gt=models.F("start_time")), name="end_after_start_slot"),
        ]

    def __str__(self):
        return f"{self.instructor.user.get_full_name()} — {self.date} {self.start_time}"


class Car(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name="cars", verbose_name="Инструктор")
    brand = models.CharField(max_length=50, verbose_name="Марка")
    model = models.CharField(max_length=50, verbose_name="Модель")
    transmission = models.CharField(max_length=3, choices=[("MT", "МКПП"), ("AT", "АКПП")], verbose_name="Коробка передач")
    plate_number = models.CharField(max_length=10, unique=True, verbose_name="Госномер")
    year = models.PositiveIntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2026)], verbose_name="Год выпуска")
    # НОВОЕ:
    photo = models.ImageField(upload_to="cars/", blank=True, null=True, verbose_name="Фото автомобиля")

    class Meta:
        verbose_name = "Учебный автомобиль"
        verbose_name_plural = "Учебные автомобили"
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate_number})"

class Booking(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="bookings", verbose_name="Курсант")
    slot = models.OneToOneField(InstructorSlot, on_delete=models.PROTECT, related_name="booking", verbose_name="Окно")
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name="bookings", verbose_name="Автомобиль")
    status = models.CharField(max_length=10, choices=[("active", "Активна"), ("cancelled", "Отменена"), ("done", "Завершена")], default="active", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий инструктора")

    class Meta:
        verbose_name = "Запись на вождение"
        verbose_name_plural = "Записи на вождение"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.slot.date} {self.slot.start_time}"


class HoursCard(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="hours_card", verbose_name="Курсант")
    hours_done = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Отработано часов")
    hours_platform = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Площадка, часов")
    hours_city = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Город, часов")
    required_hours = models.PositiveIntegerField(default=56, verbose_name="Обязательные часы")

    class Meta:
        verbose_name = "Карточка учёта вождения"
        verbose_name_plural = "Карточки учёта вождения"

    def __str__(self):
        return f"{self.student.user.get_full_name()}: {self.hours_done}/{self.required_hours}"


class InternalExam(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exams", verbose_name="Курсант")
    exam_type = models.CharField(max_length=10, choices=[("theory", "Теория"), ("practice", "Практика")], verbose_name="Тип экзамена")
    date = models.DateField(verbose_name="Дата экзамена")
    result = models.CharField(max_length=10, choices=[("pass", "Сдал"), ("fail", "Не сдал"), ("pending", "Ожидает")], default="pending", verbose_name="Результат")

    class Meta:
        verbose_name = "Внутренний экзамен"
        verbose_name_plural = "Внутренние экзамены"

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.exam_type}"


class GroupInstructor(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="group_instructors", verbose_name="Группа")
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="group_instructors", verbose_name="Инструктор")
    role = models.CharField(max_length=20, choices=[("theory", "Теория"), ("practice", "Практика")], verbose_name="Роль")

    class Meta:
        verbose_name = "Инструктор в группе"
        verbose_name_plural = "Инструкторы в группах"
        constraints = [
            models.UniqueConstraint(fields=["group", "instructor"], name="unique_group_instructor"),
        ]

    def __str__(self):
        return f"{self.group.name} — {self.instructor.user.get_full_name()} ({self.role})"



class Enrollment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="enrollment", verbose_name="Пользователь")
    group = models.ForeignKey(StudyGroup, on_delete=models.PROTECT, verbose_name="Группа")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Зачисление"
        verbose_name_plural = "Зачисления"

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.group.name} ({'Оплачено' if self.is_paid else 'Не оплачено'})"


