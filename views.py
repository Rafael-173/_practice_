import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Category, StudyGroup, Student, Branch, InstructorSlot, Booking, HoursCard, InternalExam, Car, Enrollment
from .forms import RegistrationForm

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)

def index(request):
    logger.debug("Загрузка главной страницы")
    categories = Category.objects.filter(code__in=("A", "B")).order_by("code")
    # ДЕФЕКТ 4 (Контекст): в шаблоне index.html переменная называется 'study_groups', а здесь мы передаем 'groups'
    groups = StudyGroup.objects.select_related("category", "branch").order_by("start_date")[:3]
    return render(request, "index.html", {"categories": categories, "groups": groups})

def group_list(request):
    groups = StudyGroup.objects.all()
    if request.GET.get('category'):
        groups = groups.filter(category_id=request.GET['category'])
    if request.GET.get('branch'):
        groups = groups.filter(branch_id=request.GET['branch'])
    
    return render(request, 'group_list.html', {
        'groups': groups, 
        'categories': Category.objects.all(), 
        'branches': Branch.objects.all()
    })

def group_detail(request, pk):
    # ДЕФЕКТ 2 исправлено
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

    logger.info(f"Кабинет успешно загружен для курсанта: {student.user.get_full_name()}")
    return render(request, 'cabinet.html', {
        'student': student,
        'bookings': bookings,
        'hours': hours,
        'exams': exams
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

        try:
            Booking.objects.create(
                student=student,
                slot=slot,
                car=car,
                status='active'
            )
            slot.is_booked = True
            slot.save()
            
            # ДЕФЕКТ 3 (Тип данных): пытаемся прибавить строку к числу. Если у курсанта есть карточка часов, будет TypeError.
            if hours_card := HoursCard.objects.filter(student=student).first():
                hours_card.remaining = hours_card.remaining + "5" # ОШИБКА ЗДЕСЬ
                hours_card.save()

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
        
        
        total_price = group.price 
        logger.info(f"Пользователь {request.user.username} оплатил группу. Сумма: {total_price}")
        
        messages.success(request, "Оплата прошла успешно! Вы зачислены.")
        return redirect('cabinet')
        
    return render(request, 'checkout.html', {'group': group})