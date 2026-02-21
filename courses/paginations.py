from rest_framework.pagination import PageNumberPagination


class CoursePagination(PageNumberPagination):
    """Пагинация для курсов - по 5 элементов"""
    page_size = 5
    page_size_query_param = 'page_size'  # можно менять размер через запрос
    max_page_size = 20


class LessonPagination(PageNumberPagination):
    """Пагинация для уроков - по 5 элементов"""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20
