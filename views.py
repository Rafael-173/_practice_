import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .models import (
    Category, StudyGroup, Student, Branch, InstructorSlot, 
    Booking, HoursCard, InternalExam, Car, Enrollment, Instructor
)
from .forms import RegistrationForm, InstructorLoginForm, InstructorRegistrationForm, SlotForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CarPhotoForm


logger = logging.getLogger(__name__)

class PackagePriceError(ValueError):
    """Ошибка расчёта стоимости пакета."""


def calculate_package_price(group, hours):
    """
    Считает стоимость пакета: теория + N часов вождения.
    :param group: StudyGroup
    :param hours: int или str — количество часов вождения
    :return: Decimal
    :raises PackagePriceError: если hours не число, < 0 или > 200
    """
    if hours in (None, ""):
        raise PackagePriceError("Укажите количество часов вождения")

    try:
        hours_int = int(hours)
    except (TypeError, ValueError):
        raise PackagePriceError("Количество часов должно быть целым числом")

    if hours_int < 0:
        raise PackagePriceError("Количество часов не может быть отрицательным")
    if hours_int > 200:
        raise PackagePriceError("Слишком много часов: максимум 200")

    theory = Decimal(group.price)
    hour_price = Decimal(settings.DRIVING_HOUR_PRICE)
    total = theory + hour_price * hours_int
    return total.quantize(Decimal("0.01"))


def package_price(request, pk):
    """AJAX-эндпоинт: возвращает стоимость пакета для группы и N часов."""
    group = get_object_or_404(StudyGroup, pk=pk)
    hours = request.GET.get("hours")

    try:
        total = calculate_package_price(group, hours)
    except PackagePriceError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "group_id": group.pk,
        "hours": int(hours),
        "theory_price": str(group.price),
        "hour_price": str(settings.DRIVING_HOUR_PRICE),
        "total": str(total),
    })

# --- Вход и кабинет инструктора ---
class InstructorLoginView(LoginView):
    template_name = 'instructor_login.html'
    authentication_form = InstructorLoginForm
    
    def get_success_url(self):
        return reverse_lazy('instructor_cabinet')

@login_required
def instructor_cabinet(request):
    instructor = get_object_or_404(Instructor, user=request.user)
    slots = InstructorSlot.objects.filter(instructor=instructor).order_by('date', 'start_time')
    
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.instructor = instructor
            slot.save()
            return redirect('instructor_cabinet')
    else:
        form = SlotForm()
    
    return render(request, 'instructor_schedule.html', {
        'instructor': instructor,
        'slots': slots,
        'form': form,
    })

def instructor_register(request):
    if request.user.is_authenticated:
        return redirect("instructor_cabinet")
    
    if request.method == "POST":
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация инструктора прошла успешно!")
            return redirect("instructor_cabinet")
    else:
        form = InstructorRegistrationForm()
    return render(request, "instructor_register.html", {"form": form})


# --- Остальные страницы ---
def index(request):
    logger.debug("Загрузка главной страницы")
    categories = Category.objects.filter(code__in=("A", "B")).order_by("code")
    groups = StudyGroup.objects.select_related("category", "branch").order_by("start_date")[:3]
    return render(request, "index.html", {"categories": categories, "groups": groups})

def group_list(request):
    groups = StudyGroup.objects.select_related("category", "branch").all()

    category = request.GET.get("category")
    branch = request.GET.get("branch")
    transmission = request.GET.get("transmission")  # MT / AT

    if category:
        groups = groups.filter(category_id=category)
    if branch:
        groups = groups.filter(branch_id=branch)
    if transmission in ("MT", "AT"):
        # группы, у которых есть инструктор с авто нужной КПП
        groups = groups.filter(
            group_instructors__instructor__cars__transmission=transmission
        ).distinct()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("partials/group_cards.html", {"groups": groups})
        return JsonResponse({"html": html})

    return render(request, "group_list.html", {
        "groups": groups,
        "categories": Category.objects.all(),
        "branches": Branch.objects.all(),
    })

def group_detail(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk) 
    return render(request, 'group_detail.html', {'group': group})

def policy(request):
    return render(request, 'policy.html')

@login_required
def cabinet(request):
    logger.debug(f"Загрузка кабинета для пользователя: {request.user.username}")
    
    student = Student.objects.filter(user=request.user).first()
    
    if not student:
        logger.warning(f"Пользователь {request.user.username} не является курсантом")
        messages.error(request, "Вы не являетесь курсантом автошколы.")
        return redirect('index')
        
    bookings = Booking.objects.filter(student=student).order_by('-slot__date')
    hours = HoursCard.objects.filter(student=student).first()
    exams = InternalExam.objects.filter(student=student)
    available_slots = (
    InstructorSlot.objects.filter(is_booked=False)
    .exclude(booking__isnull=False)  # исключаем те, на которые уже есть бронь
    .select_related("instructor", "instructor__user")
    .order_by("date", "start_time")[:10]
    )

    logger.info(f"Кабинет успешно загружен для курсанта: {student.user.get_full_name()}")
    return render(request, 'cabinet.html', {
        'student': student,
        'bookings': bookings,
        'hours': hours,
        'exams': exams,
        'available_slots': available_slots,
    })
    

@login_required
def booking_create(request, slot_id):
    slot = get_object_or_404(InstructorSlot, id=slot_id)
    
    if request.method == 'POST':
        logger.info(f"Курсант {request.user.username} пытается записаться на слот {slot_id}")
        
        if slot.is_booked:
            logger.warning(f"Попытка записи на уже занятый слот {slot_id}")
            messages.error(request, "Это окно уже занято. Выберите другое время.")
            return redirect('cabinet')
        
        student = Student.objects.filter(user=request.user).first()
        if not student:
            logger.warning(f"Пользователь {request.user.username} не является курсантом и не может бронировать")
            messages.error(request, "Только курсанты могут записываться на вождение.")
            return redirect('index')
            
        car = Car.objects.filter(instructor=slot.instructor).first()
        
        if not car:
            logger.error(f"У инструктора {slot.instructor} нет закрепленного автомобиля (слот {slot_id})")
            messages.error(request, "У инструктора нет закрепленного автомобиля.")
            return redirect('cabinet')

        transmission = request.POST.get("transmission") or student.transmission_type
        if transmission not in ("MT", "AT"):
            transmission = student.transmission_type

        try:
            Booking.objects.create(
                student=student,
                slot=slot,
                car=car,
                status='active',
                transmission_type=transmission,
            )
            
            

            slot.is_booked = True
            slot.save(update_fields=["is_booked"])

            logger.info(f"Успешная запись: курсант {student.user.username} на слот {slot_id}, бронь создана")
            messages.success(request, "Вы записаны на вождение!")
        except Exception as e:
            logger.error(f"Ошибка при создании брони для слота {slot_id}: {e}")
            messages.error(request, "Произошла ошибка при сохранении записи. Попробуйте позже.")
            
        return redirect('cabinet')
        
    return render(request, 'booking.html', {'slot': slot})

def prices(request):
    groups = StudyGroup.objects.all().order_by('price')
    return render(request, 'prices.html', {'groups': groups})

def contacts(request):
    return render(request, 'contacts.html')

def register(request):
    if request.user.is_authenticated:
        return redirect("cabinet")
    if request.method == "POST":
        logger.info("Попытка регистрации нового пользователя")
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"Успешная регистрация нового пользователя: {user.username}")
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect("cabinet")
        else:
            logger.warning(f"Ошибка валидации формы регистрации: {form.errors}")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})

@login_required
def checkout(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    
    if request.method == 'POST':
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            defaults={'group': group, 'is_paid': True}
        )
        
        if not created:
            enrollment.group = group
            enrollment.is_paid = True
            enrollment.save()
        
        Student.objects.get_or_create(
            user=request.user,
            defaults={
                'group': group,
                'birth_date': '2000-01-01',
                'phone': '+7 000 000-00-00',
                'transmission_type': 'MT',
                'contract_hours': 56,
            }
        )
        
        logger.info(f"Пользователь {request.user.username} оплатил группу. Сумма: {group.price}")
        messages.success(request, "Оплата прошла успешно! Вы зачислены.")
        return redirect('cabinet')
        
    return render(request, 'checkout.html', {'group': group})


@staff_member_required
def car_list(request):
    cars = Car.objects.select_related("instructor").order_by("-id")
    return render(request, "cars/list.html", {"cars": cars})


@staff_member_required
def car_upload(request):
    if request.method == "POST":
        form = CarPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            logger.info("Автомобиль добавлен: id=%s, %s %s, %s",
                        car.id, car.brand, car.model, car.plate_number)
            messages.success(request, "Автомобиль добавлен")
            return redirect("car_list")
    else:
        form = CarPhotoForm()
    return render(request, "cars/upload.html", {"form": form})