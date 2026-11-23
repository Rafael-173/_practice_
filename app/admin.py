from django.contrib import admin
from .models import (
    Category, Branch, StudyGroup, Student, Teacher, 
    Instructor, Car, InstructorSlot, Booking, HoursCard, InternalExam, GroupInstructor
)

admin.site.register(Category)
admin.site.register(Branch)
admin.site.register(StudyGroup)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Instructor)
admin.site.register(Car)
admin.site.register(InstructorSlot)
admin.site.register(Booking)
admin.site.register(HoursCard)
admin.site.register(InternalExam)
admin.site.register(GroupInstructor)