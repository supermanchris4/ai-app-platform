"""Common schema definitions shared across the API."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detail about a specific validation error."""

    field: str = Field(..., description="Field that failed validation")
    issue: str = Field(..., description="Description of the validation issue")


class ErrorResponse(BaseModel):
    """Standard error response shape per API spec."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: list[ErrorDetail] = Field(
        default=[],
        description="Field-level validation errors",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Request correlation ID",
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier",
    )


class ErrorWrapper(BaseModel):
    """Wrapper for error responses."""

    error: ErrorResponse


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    limit: int = Field(..., description="Results per page")
    has_more: bool = Field(..., description="Whether more results are available")
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for next page of results",
    )


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper."""

    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
