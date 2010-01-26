from django.contrib import admin
from apps.book.models import BookItem

#class BookItemAdmin(admin.ModelAdmin):
#    inlines = (FileInline,)
#    list_display = ('first_name', 'last_name')

admin.site.register(BookItem)

