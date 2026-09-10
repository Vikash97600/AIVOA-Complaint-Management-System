import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum, JSON, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ComplaintStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"

class RiskSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=ComplaintStatus.DRAFT,
        nullable=False,
        index=True,
    )
    qms_reference_number: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )

    # Origin & Customer Details
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    complaint_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complaint_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Product & Batch Identification
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    strength_grade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    manufacturing_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    affected_quantity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Facility & Material Impact
    manufacturing_facility: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    packaging_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Defect Analysis
    complaint_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    defect_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    complaint_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships (lazy="selectin" for async SQLAlchemy compatibility)
    risk_assessment: Mapped[Optional["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    documents: Mapped[List["ComplaintDocument"]] = relationship(
        "ComplaintDocument",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    qms_ledger: Mapped[Optional["QMSLedger"]] = relationship(
        "QMSLedger",
        back_populates="complaint",
        uselist=False,
        lazy="selectin",
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    severity_suggested: Mapped[RiskSeverity] = mapped_column(
        SQLEnum(RiskSeverity, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=RiskSeverity.MEDIUM,
        nullable=False,
    )
    complaint_category: Mapped[str] = mapped_column(String(100), nullable=False)
    suggested_next_action: Mapped[str] = mapped_column(Text, nullable=False)
    risk_details: Mapped[str] = mapped_column(Text, nullable=False)
    requires_quarantine: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="risk_assessment")


class ComplaintDocument(Base):
    __tablename__ = "complaint_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="documents")


class QMSLedger(Base):
    __tablename__ = "qms_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id"),
        nullable=False,
        unique=True,
    )
    qms_reference_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    frozen_payload_json: Mapped[Any] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="qms_ledger")
