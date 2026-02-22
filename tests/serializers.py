from rest_framework import serializers
from .models import Test, Question, AnswerOption, TestAttempt, UserAnswer, TestResult


class AnswerOptionSerializer(serializers.ModelSerializer):
    """Сериализатор для вариантов ответа"""

    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct', 'order']
        # extra_kwargs = {
        #     'is_correct': {'write_only': True}  # Не показываем правильность студентам
        # }


class AnswerOptionStudentSerializer(serializers.ModelSerializer):
    """Сериализатор для вариантов ответа (для студентов - без is_correct)"""

    class Meta:
        model = AnswerOption
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    """Сериализатор для вопросов (для преподавателей)"""
    answer_options = AnswerOptionSerializer(many=True, read_only=True, source='answers')

    class Meta:
        model = Question
        fields = ['id', 'question_type', 'text', 'points', 'order', 'explanation', 'answer_options']


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Сериализатор для вопросов (для студентов - без правильных ответов)"""
    answer_options = AnswerOptionStudentSerializer(many=True, read_only=True, source='answers')
    class Meta:
        model = Question
        fields = ['id', 'question_type', 'text', 'points', 'order', 'answer_options']

class TestSerializer(serializers.ModelSerializer):
    """Сериализатор для тестов (для преподавателей)"""
    questions = QuestionSerializer(many=True, read_only=True)
    attempts_count = serializers.IntegerField(source='attempts.count', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'lesson', 'lesson_title', 'description',
            'time_limit', 'attempts_allowed', 'passing_score', 'is_active',
            'questions', 'attempts_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


class TestListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка тестов (компактная версия)"""
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'lesson', 'lesson_title', 'description',
            'time_limit', 'attempts_allowed', 'passing_score', 'is_active',
            'questions_count'
        ]


class TestDetailStudentSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра теста студентом"""
    questions = QuestionStudentSerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'lesson', 'lesson_title', 'description',
            'time_limit', 'attempts_allowed', 'passing_score',
            'questions', 'is_active'
        ]


class TestAttemptSerializer(serializers.ModelSerializer):
    """Сериализатор для попыток прохождения теста"""
    test_title = serializers.CharField(source='test.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    time_spent = serializers.SerializerMethodField()

    class Meta:
        model = TestAttempt
        fields = [
            'id', 'test', 'test_title', 'user', 'username',
            'started_at', 'completed_at', 'status', 'score',
            'percentage', 'passed', 'time_spent'
        ]
        read_only_fields = ['user', 'started_at', 'score', 'percentage', 'passed']

    def get_time_spent(self, obj):
        """Возвращает время, затраченное на тест в минутах"""
        if obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return round(delta.total_seconds() / 60, 2)
        return None


class UserAnswerSerializer(serializers.ModelSerializer):
    """Сериализатор для ответов пользователя"""
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = UserAnswer
        fields = [
            'id', 'attempt', 'question', 'question_text',
            'selected_options', 'is_correct',
            'points_earned', 'answered_at'
        ]
        read_only_fields = ['is_correct', 'points_earned']


class SubmitAnswerSerializer(serializers.Serializer):
    """Сериализатор для отправки ответа на вопрос"""
    question_id = serializers.IntegerField(required=True)
    selected_options = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )

    def validate(self, data):
        """Валидация в зависимости от типа вопроса"""
        if not data.get('selected_options'):
            raise serializers.ValidationError("Необходимо предоставить ответ")
        return data


class TestResultSerializer(serializers.ModelSerializer):
    """Сериализатор для результатов тестов"""
    test_title = serializers.CharField(source='test.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TestResult
        fields = [
            'id', 'user', 'username', 'test', 'test_title',
            'score', 'max_score', 'percentage', 'passed', 'completed_at'
        ]


class TestSubmitSerializer(serializers.Serializer):
    """Сериализатор для отправки всех ответов"""
    answers = serializers.DictField(
        child=serializers.ListField(child=serializers.IntegerField()),
        help_text="Формат: {question_id: [answer_id1, answer_id2, ...]}"
    )
