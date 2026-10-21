"""Stable domain/application exceptions used by APIs and future tools."""


class FactoryOpsError(Exception):
    code = "FACTORYOPS_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(FactoryOpsError):
    code = "NOT_FOUND"


class ConflictError(FactoryOpsError):
    code = "CONFLICT"


class DomainRuleViolation(FactoryOpsError):
    code = "DOMAIN_RULE_VIOLATION"
