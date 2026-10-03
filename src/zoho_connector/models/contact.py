"""
Normalized domain models for Zoho Inventory Contacts.
Implements PII minimization and context protection for AI agents.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def mask_email(email: Optional[str]) -> Optional[str]:
    """Partially mask email address for PII minimization (e.g. j***e@example.com)."""
    if not email or "@" not in email:
        return email
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """Partially mask phone number for PII minimization."""
    if not phone or len(phone) < 4:
        return phone
    return "*" * (len(phone) - 4) + phone[-4:]


class ContactSummary(BaseModel):
    """Compact summary of a contact/merchant counterparty for list and search results."""

    contact_id: str = Field(description="Unique Zoho Contact ID.")
    contact_name: str = Field(description="Contact or entity name.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    contact_type: str = Field(description="Contact classification (customer, vendor).")
    status: str = Field(default="active", description="Status (active, inactive).")
    outstanding_receivable_amount: float = Field(
        default=0.0,
        description="Receivable balance due from customer.",
    )
    currency_code: Optional[str] = Field(default=None, description="Currency code.")


class ContactDetail(BaseModel):
    """Detailed representation of a contact with minimized PII."""

    contact_id: str = Field(description="Unique Zoho Contact ID.")
    contact_name: str = Field(description="Contact or entity name.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    contact_type: str = Field(description="Contact classification (customer, vendor).")
    status: str = Field(default="active", description="Status (active, inactive).")
    email: Optional[str] = Field(default=None, description="Contact email address.")
    phone: Optional[str] = Field(default=None, description="Contact phone number.")
    outstanding_receivable_amount: float = Field(
        default=0.0,
        description="Outstanding balance owed to merchant.",
    )
    outstanding_payable_amount: float = Field(
        default=0.0,
        description="Outstanding balance owed by merchant.",
    )
    currency_code: Optional[str] = Field(default=None, description="Currency code.")
    city: Optional[str] = Field(default=None, description="Billing/primary city.")
    country: Optional[str] = Field(default=None, description="Billing/primary country.")
    created_time: Optional[str] = Field(default=None, description="Record creation timestamp.")


def normalize_contact_summary(raw: Dict[str, Any]) -> ContactSummary:
    """Project raw Zoho contact record into ContactSummary."""
    return ContactSummary(
        contact_id=str(raw.get("contact_id", "")),
        contact_name=str(raw.get("contact_name") or ""),
        company_name=raw.get("company_name"),
        contact_type=str(raw.get("contact_type") or "customer"),
        status=str(raw.get("status") or "active"),
        outstanding_receivable_amount=float(raw.get("outstanding_receivable_amount") or 0.0),
        currency_code=raw.get("currency_code"),
    )


def normalize_contact_detail(raw: Dict[str, Any], mask_pii: bool = False) -> ContactDetail:
    """Project raw Zoho contact record into ContactDetail with optional PII masking."""
    email = raw.get("email")
    phone = raw.get("phone") or raw.get("mobile")

    if mask_pii:
        email = mask_email(email)
        phone = mask_phone(phone)

    # Extract primary address city/country if present
    billing_address = raw.get("billing_address") or {}
    city = billing_address.get("city") or raw.get("city")
    country = billing_address.get("country") or raw.get("country")

    return ContactDetail(
        contact_id=str(raw.get("contact_id", "")),
        contact_name=str(raw.get("contact_name") or ""),
        company_name=raw.get("company_name"),
        contact_type=str(raw.get("contact_type") or "customer"),
        status=str(raw.get("status") or "active"),
        email=email,
        phone=phone,
        outstanding_receivable_amount=float(raw.get("outstanding_receivable_amount") or 0.0),
        outstanding_payable_amount=float(raw.get("outstanding_payable_amount") or 0.0),
        currency_code=raw.get("currency_code"),
        city=city,
        country=country,
        created_time=raw.get("created_time"),
    )
