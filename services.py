from django.conf import settings
from django.core.mail import send_mail


def send_booking_email(student, booking):
    if not student.user.email:
        return
    subject = "Вы записаны на вождение"
    message = (
        f"Здравствуйте, {student.user.get_full_name() or student.user.username}!\n\n"
        f"Вы записаны на вождение:\n"
        f"Дата: {booking.slot.date}\n"
        f"Время: {booking.slot.start_time}–{booking.slot.end_time}\n"
        f"Инструктор: {booking.slot.instructor.user.get_full_name()}\n"
        f"Автомобиль: {booking.car.brand} {booking.car.model} ({booking.car.plate_number})\n"
        f"КПП: {booking.get_transmission_type_display()}\n\n"
        f"Автошкола «Автолайн»"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.user.email], fail_silently=False)