"""Non-counting pagination for the high-volume persons directory."""
from rest_framework.pagination import CursorPagination


class PersonCursorPagination(CursorPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-created_at", "-pk")

    def get_ordering(self, request, queryset, view):
        # Use only the ordering already validated by the directory view.
        return tuple(queryset.query.order_by) or self.ordering
