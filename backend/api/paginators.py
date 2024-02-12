from rest_framework.pagination import PageNumberPagination

from foodgram import constants


class LimitPagination(PageNumberPagination):
    page_size = constants.PAGE_SIZE
    page_size_query_param = 'limit'
