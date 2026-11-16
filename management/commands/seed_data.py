import random
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import (
    Category, Branch, StudyGroup, Student, Teacher, Instructor, 
    Car, InstructorSlot, Booking, HoursCard, InternalExam, GroupInstructor
)

class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными для автошколы (10 сущностей)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинаем заполнение базы...")

        # 1. Категории
        categories = []
        for code, name in [("A", "Мотоцикл"), ("B", "Легковой автомобиль")]:
            cat, _ = Category.objects.get_or_create(code=code, defaults={"name": name})
            categories.append(cat)

        # 2. Филиалы
        branches = []
        for i in range(1, 4):
            br, _ = Branch.objects.get_or_create(
                name=f"Филиал №{i}", 
                defaults={"address": f"ул. Ленина, д. {i*10}", "phone": f"+7 999 000-00-0{i}"}
            )
            branches.append(br)

        # 3. Учебные группы (5 штук)
        groups = []
        for i in range(1, 6):
            cat = random.choice(categories)
            br = random.choice(branches)
            start = date(2026, 2, 1) + timedelta(days=i*10)
            group, _ = StudyGroup.objects.get_or_create(
                branch=br, name=f"Группа-{i}",
                defaults={
                    "category": cat,
                    "start_date": start,
                    "end_date": start + timedelta(days=60),
                    "price": random.randint(30000, 45000),
                    "max_students": 25
                }
            )
            groups.append(group)

        # 4. Преподаватели теории (3 штуки)
        teachers = []
        for i in range(1, 4):
            username = f"teacher_{i}"
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("password123")
                user.first_name = "Иван"
                user.last_name = f"Теоретиков_{i}"
                user.save()
            t, _ = Teacher.objects.get_or_create(user=user, defaults={"specialization": "ПДД"})
            teachers.append(t)

        # 5. Инструкторы (10 штук)
        instructors = []
        for i in range(1, 11):
            username = f"instructor_{i}"
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("password123")
                user.first_name = "Петр"
                user.last_name = f"Инструкторов_{i}"
                user.save()
            
            inst, _ = Instructor.objects.get_or_create(
                user=user,
                defaults={
                    "branch": random.choice(branches),
                    "experience_years": random.randint(1, 20),
                    "rating": round(random.uniform(3.5, 5.0), 2)
                }
            )
            instructors.append(inst)

            # Связка M2M (инструктор в группе)
            GroupInstructor.objects.get_or_create(
                group=random.choice(groups),
                instructor=inst,
                defaults={"role": random.choice(["theory", "practice"])}
            )

        # 6. Курсанты (30 штук)
        students = []
        for i in range(1, 31):
            username = f"student_{i}"
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("password123")
                user.first_name = "Сидор"
                user.last_name = f"Курсантов_{i}"
                user.save()
            
            trans = random.choice(["MT", "AT"])
            stud, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    "group": random.choice(groups),
                    "birth_date": date(1990, 1, 1) + timedelta(days=random.randint(0, 8000)),
                    "phone": f"+7 911 111-11-{i:02d}",
                    "transmission_type": trans,
                    "contract_hours": 56,
                    "license_passed": random.choice([True, False])
                }
            )
            students.append(stud)

            # 7. Карточка учёта вождения (для каждого курсанта)
            HoursCard.objects.get_or_create(
                student=stud,
                defaults={
                    "hours_done": round(random.uniform(0, 56), 1),
                    "required_hours": 56
                }
            )

        # 8. Автомобили (10 штук)
        cars = []
        for i in range(1, 11):
            car, _ = Car.objects.get_or_create(
                plate_number=f"А{100+i}ВС77",
                defaults={
                    "instructor": random.choice(instructors),
                    "brand": random.choice(["Lada", "Kia", "Hyundai"]),
                    "model": random.choice(["Vesta", "Rio", "Solaris"]),
                    "transmission": random.choice(["MT", "AT"]),
                    "year": random.randint(2015, 2024)
                }
            )
            cars.append(car)

        # 9. Окна инструкторов и Записи (30 окон, 20 записей)
        for i in range(30):
            inst = random.choice(instructors)
            slot_date = date(2026, 2, 10) + timedelta(days=i % 10)
            
            start_hour = 9 + (i % 8)
            start_t = time(start_hour, 0)
            end_t = time(start_hour + 1, 30)
            
            slot, _ = InstructorSlot.objects.get_or_create(
                instructor=inst, 
                date=slot_date, 
                start_time=start_t,
                defaults={"end_time": end_t}
            )

            if i % 2 == 0:
                slot.is_booked = True
                slot.save()
                Booking.objects.get_or_create(
                    slot=slot,
                    defaults={
                        "student": random.choice(students),
                        "car": random.choice(cars),
                        "status": random.choice(["active", "done", "cancelled"]),
                        "comment": "Отработали парковку" if random.choice([True, False]) else ""
                    }
                )

        # 10. Внутренние экзамены (15 штук)
        for i in range(15):
            stud = random.choice(students)
            InternalExam.objects.get_or_create(
                student=stud,
                exam_type=random.choice(["theory", "practice"]),
                date=date(2026, 3, 1) + timedelta(days=i),
                defaults={
                    "result": random.choice(["pass", "fail", "pending"])
                }
            )

        self.stdout.write(self.style.SUCCESS("База успешно заполнена! Все 10 сущностей."))