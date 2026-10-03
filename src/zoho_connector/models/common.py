"""
Common models for pagination, truncation, and agent context-window protection.
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """Metadata describing pagination status of a list response."""

    page: int = Field(ge=1, description="Current page number (1-indexed).")
    per_page: int = Field(ge=1, description="Number of items requested per page.")
    has_more: bool = Field(description="True if more pages are available.")
    total_count: Optional[int] = Field(
        default=None,
        description="Total items available across all pages, if provided by Zoho API.",
    )


class TruncationMetadata(BaseModel):
    """Metadata indicating if response was bounded/truncated to protect model context window."""

    is_truncated: bool = Field(
        default=False,
        description="True if results were capped to protect the context window.",
    )
    truncated_reason: Optional[str] = Field(
        default=None,
        description="Reason why response was truncated.",
    )
    total_returned: int = Field(
        description="Number of records returned in this response.",
    )
    has_more: bool = Field(
        description="Indicates if additional unreturned records exist.",
    )
    next_page_instruction: Optional[str] = Field(
        default=None,
        description="Guidance for the AI agent on how to retrieve the next page.",
    )


class BoundedListResponse(BaseModel, Generic[T]):
    """Standardized normalized response for all list operations."""

    items: List[T] = Field(description="List of normalized records.")
    pagination: PaginationMetadata = Field(description="Pagination state.")
    truncation: TruncationMetadata = Field(description="Context window protection status.")
