from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'per_page'
    max_page_size = 100

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        per_page = self.get_page_size(self.request)
        total_pages = math.ceil(total_items / per_page) if per_page else 0
        current_page = self.page.number

        return Response({
            "success": True,
            "current_page": current_page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "data": data
        })
