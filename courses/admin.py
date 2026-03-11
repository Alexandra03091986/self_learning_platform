from django.contrib import admin

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админка для курсов"""

    list_display = ("id", "title", "owner", "created_at")
    list_filter = ("owner", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админка для уроков"""

    list_display = ("id", "title", "course", "owner", "order")
    list_filter = ("course", "owner")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
