from rest_framework.pagination import PageNumberPagination


class CastomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
