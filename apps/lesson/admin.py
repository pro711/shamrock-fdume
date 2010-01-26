from django.contrib import admin
from apps.lesson.models import Lesson, LessonComment


admin.site.register(Lesson)
admin.site.register(LessonComment)

