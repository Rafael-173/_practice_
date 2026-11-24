from datetime import date, time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, time, timedelta
from django.utils import timezone

from app.models import (
    Category, Branch, StudyGroup, Student, Teacher, Instructor,
    Car, InstructorSlot, Booking, HoursCard, InternalExam,
    GroupInstructor, Enrollment,
)


class Command(BaseCommand):
    help = "Идемпотентно создаёт тестовые данные для занятий 13–17 (все 10 сущностей, без явных pk)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Заполняем тестовые данные...")
        today = timezone.now().date()


        # ---------- 1. Пользователи ----------
        users = {}
        for username, first, last, email in [
            ("student1",    "Иван",  "Курсантов",     "student1@example.com"),
            ("student2",    "Пётр",  "Безпрофиля",    "student2@example.com"),
            ("instructor1", "Сергей","Инструкторов",  "instructor1@example.com"),
            ("instructor2", "Олег",  "Автоматов",     "instructor2@example.com"),
            ("teacher1",    "Иван",  "Теоретиков",    "teacher1@example.com"),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "email": email},
            )
            user.set_password("Test12345!")
            user.first_name = first
            user.last_name = last
            user.email = email
            user.is_active = True
            user.save()
            users[username] = user
            self.stdout.write(f"  user {username}: {'created' if created else 'updated'}")

        # ---------- 2. Категории ----------
        categories = {}
        for code, name in [("A", "Мотоцикл"), ("B", "Легковой автомобиль")]:
            obj, _ = Category.objects.update_or_create(code=code, defaults={"name": name})
            categories[code] = obj
        self.stdout.write(f"  categories: {len(categories)}")

        # ---------- 3. Филиалы ----------
        branches = {}
        for name, address, phone in [
            ("Филиал №1", "ул. Ленина, д. 10", "+7 999 000-00-01"),
            ("Филиал №2", "ул. Ленина, д. 20", "+7 999 000-00-02"),
        ]:
            obj, _ = Branch.objects.update_or_create(
                name=name, defaults={"address": address, "phone": phone},
            )
            branches[name] = obj
        self.stdout.write(f"  branches: {len(branches)}")

        # ---------- 4. Учебные группы ----------
        group_specs = [
            ("Филиал №1", "Группа-1", "A", today + timedelta(days=10),  today + timedelta(days=70),  "30000.00", 25),
            ("Филиал №2", "Группа-2", "A", today + timedelta(days=20),  today + timedelta(days=80),  "35000.00", 25),
            ("Филиал №1", "Группа-3", "B", today + timedelta(days=30),  today + timedelta(days=90),  "40000.00", 20),
            ("Филиал №2", "Группа-4", "B", today + timedelta(days=40),  today + timedelta(days=100), "45000.00", 20),
        ]
        groups = {}
        for branch_name, name, cat_code, start, end, price, max_students in group_specs:
            obj, _ = StudyGroup.objects.update_or_create(
                branch=branches[branch_name],
                name=name,
                defaults={
                    "category": categories[cat_code],
                    "start_date": start,
                    "end_date": end,
                    "price": price,
                    "max_students": max_students,
                },
            )
            groups[name] = obj
        self.stdout.write(f"  groups: {len(groups)}")

        # ---------- 5. Преподаватель теории ----------
        teacher, _ = Teacher.objects.update_or_create(
            user=users["teacher1"],
            defaults={"specialization": "ПДД"},
        )
        self.stdout.write("  teacher: 1")

        # ---------- 6. Инструкторы ----------
        instructor1, _ = Instructor.objects.update_or_create(
            user=users["instructor1"],
            defaults={"branch": branches["Филиал №1"], "experience_years": 5, "rating": "4.80"},
        )
        instructor2, _ = Instructor.objects.update_or_create(
            user=users["instructor2"],
            defaults={"branch": branches["Филиал №2"], "experience_years": 3, "rating": "4.50"},
        )
        self.stdout.write("  instructors: 2")

        # ---------- 7. Инструкторы в группах (GroupInstructor) ----------
        
        gi_specs = [
            ("Группа-1", instructor1),  # A × Ф1, МТ
            ("Группа-2", instructor2),  # A × Ф2, АТ
            ("Группа-3", instructor1),  # B × Ф1, МТ
            ("Группа-4", instructor2),  # B × Ф2, АТ
        ]
        for group_name, instr in gi_specs:
            GroupInstructor.objects.update_or_create(
                group=groups[group_name],
                instructor=instr,
                defaults={"role": "practice"},
            )
        self.stdout.write(f"  group_instructors: {len(gi_specs)} (все 4 группы)")

                # ---------- 8. Автомобили ----------
        car_mt, _ = Car.objects.update_or_create(
            plate_number="А101ВС77",
            defaults={
                "instructor": instructor1,
                "brand": "Lada", "model": "Vesta",
                "transmission": "MT", "year": 2022,
            },
        )
        car_at, _ = Car.objects.update_or_create(
            plate_number="А102ВС77",
            defaults={
                "instructor": instructor2,
                "brand": "Kia", "model": "Rio",
                "transmission": "AT", "year": 2023,
            },
        )
                
        Car.objects.update_or_create(
            plate_number="А103ВС77",
            defaults={
                "instructor": instructor1,
                "brand": "Renault", "model": "Logan",
                "transmission": "AT", "year": 2023,
            },
        )
        Car.objects.update_or_create(
            plate_number="А104ВС77",
            defaults={
                "instructor": instructor2,
                "brand": "Hyundai", "model": "Solaris",
                "transmission": "MT", "year": 2022,
            },
        )

        # ---------- 9. Окна инструктора 1 ----------
        slot_free, _ = InstructorSlot.objects.update_or_create(
            instructor=instructor1, date=today + timedelta(days=3), start_time=time(10, 0),
            defaults={"end_time": time(11, 30), "is_booked": False},
        )
        slot_busy, _ = InstructorSlot.objects.update_or_create(
            instructor=instructor1, date=today + timedelta(days=1), start_time=time(12, 0),
            defaults={"end_time": time(13, 30), "is_booked": True},
        )
        self.stdout.write("  slots instructor1: 2 (1 free, 1 busy)")

        # ---------- 10. Окна инструктора 2 (AT) ----------
        slot_at_free, _ = InstructorSlot.objects.update_or_create(
            instructor=instructor2, date=today + timedelta(days=4), start_time=time(10, 0),
            defaults={"end_time": time(11, 30), "is_booked": False},
        )
        slot_at_busy, _ = InstructorSlot.objects.update_or_create(
            instructor=instructor2, date=today + timedelta(days=2), start_time=time(12, 0),
            defaults={"end_time": time(13, 30), "is_booked": True},
        )
        self.stdout.write("  slots instructor2: 2 (1 free, 1 busy)")

        # ---------- 11. Курсант с профилем ----------
        student, _ = Student.objects.update_or_create(
            user=users["student1"],
            defaults={
                "group": groups["Группа-1"],
                "birth_date": date(2000, 1, 1),
                "phone": "+7 900 000-00-02",
                "transmission_type": "MT",
                "contract_hours": 56,
                "license_passed": False,
            },
        )
        # student2 намеренно без профиля Student — для TC-15
        if hasattr(users["student2"], "student"):
            users["student2"].student.delete()
        self.stdout.write("  students: 1 (student2 без профиля — для TC-15)")

        # ---------- 12. Карточка часов ----------
        HoursCard.objects.update_or_create(
            student=student,
            defaults={
                "hours_done": "15.00",
                "hours_platform": "10.00",
                "hours_city": "5.00",
                "required_hours": 56,
            },
        )
        self.stdout.write("  hourscard: 1 (15 ч: 10 площадка + 5 город)")

        # ---------- 13. Брони ----------
        # активная — на занятый слот instructor1 (для TC-17, TC-31)
        Booking.objects.update_or_create(
            slot=slot_busy,
            defaults={
                "student": student,
                "car": car_mt,
                "status": "active",
                "comment": "Отработали парковку",
            },
        )
        # завершённая — для TC-27/TC-28 (карточка вождения с комментарием)
        Booking.objects.update_or_create(
            slot=slot_at_busy,
            defaults={
                "student": student,
                "car": car_at,
                "status": "done",
                "comment": "Город: перекрёстки, разворот",
            },
        )
        self.stdout.write("  bookings: 2 (active + done)")

        # ---------- 14. Внутренние экзамены ----------
        for exam_type, exam_date, result in [
            ("theory",   today + timedelta(days=15), "pass"),
            ("practice", today + timedelta(days=45), "pending"),
        ]:
            InternalExam.objects.update_or_create(
                student=student,
                exam_type=exam_type,
                date=exam_date,
                defaults={"result": result},
            )
        self.stdout.write("  internal_exams: 2 (theory pass, practice pending)")

        # ---------- 15. Зачисление ----------
        Enrollment.objects.update_or_create(
            user=users["student1"],
            defaults={"group": groups["Группа-1"], "is_paid": True},
        )
        self.stdout.write("  enrollment: 1 (student1, paid)")

        self.stdout.write(self.style.SUCCESS("Готово. Все 10 сущностей на месте."))