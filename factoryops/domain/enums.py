"""Enumerations shared by the domain, persistence, and API boundaries."""

from enum import StrEnum


class LifecycleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SupplierRiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InspectionResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class QualitySeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QualityIssueStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    CLOSED = "CLOSED"


class QualityCaseStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    CLOSED = "CLOSED"


class CasePriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CorrectiveActionStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DocumentType(StrEnum):
    SOP = "SOP"
    FMEA = "FMEA"
    EIGHT_D = "8D"
    QUALITY_STANDARD = "QUALITY_STANDARD"
    INSPECTION_GUIDE = "INSPECTION_GUIDE"
    OTHER = "OTHER"


class UserRole(StrEnum):
    VIEWER = "VIEWER"
    QUALITY_ENGINEER = "QUALITY_ENGINEER"
    SUPPLY_ENGINEER = "SUPPLY_ENGINEER"
    ADMIN = "ADMIN"
