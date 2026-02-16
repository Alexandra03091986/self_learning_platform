from django.contrib import admin
from .models import Test, Question, AnswerOption, TestAttempt, UserAnswer, TestResult


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    show_change_link = True
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'is_active', 'time_limit', 'attempts_allowed', 'created_at')
    list_filter = ('is_active', 'lesson', 'created_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type', 'points', 'order')
    list_filter = ('question_type', 'test')
    search_fields = ('text',)
    inlines = [AnswerOptionInline]


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('test', 'user', 'status', 'percentage', 'passed', 'started_at')
    list_filter = ('status', 'passed', 'test', 'user')
    readonly_fields = ('started_at', 'completed_at')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_earned')
    list_filter = ('is_correct', 'attempt__test')
    readonly_fields = ('answered_at',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'percentage', 'passed', 'completed_at']
    list_filter = ['passed', 'test']
    readonly_fields = ['completed_at']
