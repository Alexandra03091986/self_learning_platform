from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('-id',)

    # Для страницы РЕДАКТИРОВАНИЯ
    fieldsets = UserAdmin.fieldsets + (
        ('Роль и дополнительная информация', {
            'fields': ('role', 'avatar', 'bio'),
        }),
    )
    # Для страницы СОЗДАНИЯ
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Роль и дополнительная информация', {
            'fields': ('role', 'avatar', 'bio'),
        }),
    )
