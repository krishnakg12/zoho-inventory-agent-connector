"""
Base service layer helpers for pagination validation, field projection,
and context-window protection.
"""

import json
from typing import Any, Callable, List, Optional, TypeVar
from pydantic import BaseModel

from zoho_connector.config import Settings
from zoho_connector.errors import ValidationError
from zoho_connector.models.common import (
    BoundedListResponse,
    PaginationMetadata,
    TruncationMetadata,
)

T = TypeVar("T", bound=BaseModel)


class BaseDataService:
    """Base service providing common input normalization and context window bounds."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def normalize_pagination_params(
        self,
        page: Optional[int],
        per_page: Optional[int],
    ) -> tuple[int, int]:
        """Validate and bound page and per_page parameters."""
        p = 1 if page is None or page < 1 else int(page)

        if per_page is None:
            pp = self.settings.default_page_size
        else:
            pp = int(per_page)

        if pp < 1:
            raise ValidationError("per_page must be at least 1", field="per_page")
        if pp > self.settings.max_page_size:
            pp = self.settings.max_page_size

        return p, pp

    def build_bounded_response(
        self,
        items: List[T],
        page: int,
        per_page: int,
        has_more_upstream: bool,
        total_count: Optional[int],
        item_type_label: str = "records",
        next_query_params: Optional[dict] = None,
    ) -> BoundedListResponse[T]:
        """
        Build normalized BoundedListResponse with strict byte budget enforcement.
        If response exceeds max_response_bytes, safely trims records and supplies
        explicit truncation metadata rather than silently clipping or blowing the context window.
        """
        original_count = len(items)
        max_bytes = self.settings.max_response_bytes

        # Check serialized size
        serialized = json.dumps([item.model_dump() for item in items])
        is_truncated = False
        truncated_reason = None
        has_more = has_more_upstream

        if len(serialized.encode("utf-8")) > max_bytes and len(items) > 1:
            # Progressively trim items to fit within budget
            trimmed_items = list(items)
            while trimmed_items and len(json.dumps([i.model_dump() for i in trimmed_items]).encode("utf-8")) > max_bytes:
                trimmed_items.pop()

            if not trimmed_items and items:
                # Keep at least 1 item even if single item is large
                trimmed_items = [items[0]]

            items = trimmed_items
            is_truncated = True
            has_more = True
            truncated_reason = (
                f"Response exceeded {max_bytes} bytes context budget. "
                f"Reduced from {original_count} to {len(items)} {item_type_label}."
            )

        instruction = None
        if has_more:
            next_page = page + 1
            instruction = f"More unread {item_type_label} exist. Request next page with page={next_page} and per_page={per_page}."

        pagination = PaginationMetadata(
            page=page,
            per_page=per_page,
            has_more=has_more,
            total_count=total_count,
        )

        truncation = TruncationMetadata(
            is_truncated=is_truncated,
            truncated_reason=truncated_reason,
            total_returned=len(items),
            has_more=has_more,
            next_page_instruction=instruction,
        )

        return BoundedListResponse(
            items=items,
            pagination=pagination,
            truncation=truncation,
        )
