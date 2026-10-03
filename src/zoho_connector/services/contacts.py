"""
Service layer for Zoho Inventory Contacts.
Handles argument normalization, field projection, PII minimization, and context-window protection.
"""

from typing import Any, Dict, Optional

from zoho_connector.clients.base import ZohoClientProtocol
from zoho_connector.config import Settings
from zoho_connector.errors import NotFoundError, ValidationError
from zoho_connector.models.common import BoundedListResponse
from zoho_connector.models.contact import (
    ContactDetail,
    ContactSummary,
    normalize_contact_detail,
    normalize_contact_summary,
)
from zoho_connector.services.base import BaseDataService

VALID_CONTACT_TYPES = {"customer", "vendor", "all"}
VALID_CONTACT_STATUSES = {"active", "inactive", "all"}


class ContactService(BaseDataService):
    """Manages business operations for Zoho Inventory Contacts with PII minimization."""

    def __init__(self, client: ZohoClientProtocol, settings: Settings):
        super().__init__(settings=settings)
        self.client = client

    async def list_contacts(
        self,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
        contact_type: Optional[str] = "customer",
        status: Optional[str] = "active",
    ) -> BoundedListResponse[ContactSummary]:
        """Retrieve paginated contacts/customers with minimized fields."""
        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "page": page_num,
            "per_page": page_size,
        }

        if contact_type:
            norm_type = contact_type.strip().lower()
            if norm_type not in VALID_CONTACT_TYPES:
                raise ValidationError(
                    f"Invalid contact_type '{contact_type}'. Allowed: {list(VALID_CONTACT_TYPES)}",
                    field="contact_type",
                )
            if norm_type != "all":
                params["contact_type"] = norm_type

        if status:
            norm_status = status.strip().lower()
            if norm_status not in VALID_CONTACT_STATUSES:
                raise ValidationError(
                    f"Invalid status '{status}'. Allowed: {list(VALID_CONTACT_STATUSES)}",
                    field="status",
                )
            if norm_status != "all":
                params["status"] = norm_status

        raw_response = await self.client.list_contacts(params)
        raw_contacts = raw_response.get("contacts", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_contact_summary(c) for c in raw_contacts]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="contacts",
        )

    async def get_contact(self, contact_id: str, mask_pii: bool = False) -> ContactDetail:
        """Retrieve detailed contact info with PII controls."""
        if not contact_id or not contact_id.strip():
            raise ValidationError("contact_id must be provided and non-empty", field="contact_id")

        raw_response = await self.client.get_contact(contact_id.strip())
        raw_contact = raw_response.get("contact")
        if not raw_contact:
            raise NotFoundError("Contact", contact_id)

        return normalize_contact_detail(raw_contact, mask_pii=mask_pii)

    async def search_contacts(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        email: Optional[str] = None,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
    ) -> BoundedListResponse[ContactSummary]:
        """Search contacts by name, company, or email."""
        if not any([name, company, email]):
            raise ValidationError("At least one search filter (name, company, email) must be specified.")

        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "page": page_num,
            "per_page": page_size,
        }

        if name:
            params["contact_name_contains"] = name.strip()
        if company:
            params["company_name_contains"] = company.strip()
        if email:
            params["email_contains"] = email.strip()

        raw_response = await self.client.list_contacts(params)
        raw_contacts = raw_response.get("contacts", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_contact_summary(c) for c in raw_contacts]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="contacts",
        )
