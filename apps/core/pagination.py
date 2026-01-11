"""
Custom pagination classes for HunarMitra APIs.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class for all list APIs.
    
    Provides consistent response format:
    {
        "count": 125,
        "next_page": 2,
        "prev_page": null,
        "results": [...]
    }
    
    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 50)
    """
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 50
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """Return paginated response with custom format."""
        return Response({
            'count': self.page.paginator.count,
            'next_page': self.page.next_page_number() if self.page.has_next() else None,
            'prev_page': self.page.previous_page_number() if self.page.has_previous() else None,
            'results': data
        })
