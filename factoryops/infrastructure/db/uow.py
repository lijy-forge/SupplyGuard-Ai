"""SQLAlchemy unit of work for atomic application use cases."""

from types import TracebackType

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from factoryops.application.ports import AbstractUnitOfWork
from factoryops.domain.exceptions import ConflictError

from .repositories import (
    SqlAlchemyBatchRepository,
    SqlAlchemyInspectionRepository,
    SqlAlchemyPartRepository,
    SqlAlchemyQualityCaseRepository,
    SqlAlchemySupplierRepository,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.suppliers = SqlAlchemySupplierRepository(self.session)
        self.parts = SqlAlchemyPartRepository(self.session)
        self.batches = SqlAlchemyBatchRepository(self.session)
        self.inspections = SqlAlchemyInspectionRepository(self.session)
        self.quality_cases = SqlAlchemyQualityCaseRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.session is None:
            return
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        assert self.session is not None
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "A record with the same business key or relationship already exists"
            ) from exc

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()
