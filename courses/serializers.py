from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source="owner", read_only=True)
    students_count = serializers.IntegerField(source="students.count", read_only=True)
    lesson_count = serializers.IntegerField(source="lesson.count", read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ("owner", "created_at", "updated_at")


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")
