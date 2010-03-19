from django.contrib import admin
from apps.lesson.models import Lesson, LessonComment, LessonCommentFetcher


admin.site.register(Lesson)
admin.site.register(LessonComment)
admin.site.register(LessonCommentFetcher)

