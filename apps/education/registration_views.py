from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.education.registration_permissions import RegistrationAccess
from apps.education.registration_selectors import (
    RegistrationFilters,
    RegistrationScope,
    entity_context,
    list_registrations,
    picker_options,
    registration_detail,
)
from apps.reports.selectors.reports import ReportFilterError


def _bad_filter(exc):
    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class RegistrationDirectoryView(APIView):
    permission_classes = (RegistrationAccess,)

    def get(self, request):
        scope = RegistrationScope(request.user)
        try:
            filters = RegistrationFilters.parse(request.query_params)
            return Response(list_registrations(scope, filters, request.query_params))
        except ReportFilterError as exc:
            return _bad_filter(exc)


class RegistrationContextView(APIView):
    permission_classes = (RegistrationAccess,)

    def get(self, request, kind, pk):
        scope = RegistrationScope(request.user)
        try:
            context = entity_context(scope, kind, pk)
            params = request.query_params.copy()
            params.update(context["filters"])
            filters = RegistrationFilters.parse(params)
            context["registrations"] = list_registrations(scope, filters, params)
            return Response(context)
        except ReportFilterError as exc:
            return _bad_filter(exc)


class RegistrationRecordDetailView(APIView):
    permission_classes = (RegistrationAccess,)

    def get(self, request, source, pk):
        try:
            return Response(registration_detail(RegistrationScope(request.user), source, pk))
        except ReportFilterError as exc:
            return _bad_filter(exc)


class RegistrationPickerView(APIView):
    permission_classes = (RegistrationAccess,)

    def get(self, request):
        try:
            return Response(picker_options(RegistrationScope(request.user), request.query_params))
        except ReportFilterError as exc:
            return _bad_filter(exc)