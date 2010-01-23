from django.contrib import admin
from apps.book.models import User, BookItem, Course

#class BookItemAdmin(admin.ModelAdmin):
#    inlines = (FileInline,)
#    list_display = ('first_name', 'last_name')

admin.site.register(BookItem)
admin.site.register(User)
admin.site.register(Course)
