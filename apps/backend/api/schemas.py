"""
DeepFeed AI - API Response Envelope
All API responses follow the standard format defined in TDS §7.2:
  Success: { "trace_id": "uuid", "data": {} }
  Error:   { "trace_id": "uuid", "error": { "code": "...", "message": "...", "details": {} } }
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class APIResponse(BaseModel, Generic[T]):
    trace_id: str
    data: Optional[T] = None


class APIErrorResponse(BaseModel):
    trace_id: str
    error: ErrorDetail


def success_response(data: Any, trace_id: str) -> dict:
    return {"trace_id": trace_id, "data": data}


def error_response(code: str, message: str, trace_id: str, details: Optional[dict] = None) -> dict:
    return {
        "trace_id": trace_id,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
