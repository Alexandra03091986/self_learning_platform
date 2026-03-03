from rest_framework.pagination import PageNumberPagination


class TestPagination(PageNumberPagination):
    """Пагинация для тестов - по 5 элементов"""

    page_size = 5
    page_size_query_param = "page_size"  # можно менять размер через запрос
    max_page_size = 20


class TestResultPagination(PageNumberPagination):
    """Пагинация для результатов тестов"""

    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100
