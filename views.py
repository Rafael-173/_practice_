from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Category, StudyGroup, Student, Branch, InstructorSlot, Booking, HoursCard, InternalExam
from .forms import RegistrationForm

def index(request):
    categories = Category.objects.filter(code__in=("A", "B")).order_by("code")
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
    group = get_object_or_404(StudyGroup, pk=pk)
    return render(request, 'group_detail.html', {'group': group})

def policy(request):
    return render(request, 'policy.html')

@login_required
def cabinet(request):
    # Ищем курсанта по текущему пользователю
    student = Student.objects.filter(user=request.user).first()
    
    if not student:
        messages.error(request, "Вы не являетесь курсантом автошколы.")
        return redirect('index')
        
    bookings = Booking.objects.filter(student=student).order_by('-slot__date')
    hours = HoursCard.objects.filter(student=student).first()
    exams = InternalExam.objects.filter(student=student)

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
        # 1. Проверяем, не занято ли уже это окно
        if slot.is_booked:
            messages.error(request, "Это окно уже занято. Выберите другое время.")
            return redirect('cabinet')
        
        # 2. Получаем курсанта
        student = Student.objects.filter(user=request.user).first()
        if not student:
            messages.error(request, "Только курсанты могут записываться на вождение.")
            return redirect('index')
            
        # 3. Создаем запись
        # Примечание: в модели Booking есть поле car (автомобиль). 
        # Если в форме его нет, нужно выбрать первый доступный автомобиль инструктора.
        car = student.group.instructors.first().cars.first() if hasattr(student.group, 'instructors') else None
        
        # Для упрощения берем первую машину инструктора, если она есть
        from .models import Car
        car = Car.objects.filter(instructor=slot.instructor).first()
        
        if not car:
            messages.error(request, "У инструктора нет закрепленного автомобиля.")
            return redirect('cabinet')

        Booking.objects.create(
            student=student,
            slot=slot,
            car=car,
            status='active'
        )
        
        # 4. Помечаем окно как занятое
        slot.is_booked = True
        slot.save()
        
        messages.success(request, "Вы записаны на вождение!")
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
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect("cabinet")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})
