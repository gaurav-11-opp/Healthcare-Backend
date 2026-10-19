import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return every API error in one shape: {"status_code": int, "errors": ...}."""
    if isinstance(exc, IntegrityError):
        logger.warning("IntegrityError: %s", exc)
        return Response(
            {"status_code": 409, "errors": {"detail": "Conflict with existing data."}},
            status=status.HTTP_409_CONFLICT,
        )

    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"status_code": response.status_code, "errors": response.data}
    return response
