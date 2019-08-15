from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from typing_extensions import final

from app.commons.database.infra import DB
from app.payout.repository.bankdb.base import PayoutBankDBRepository
from app.payout.repository.bankdb.model import payouts
from app.payout.repository.bankdb.model.payout import PayoutEntity, PayoutCreate


class PayoutRepositoryInterface(ABC):
    @abstractmethod
    async def create_payout(self, data: PayoutCreate) -> PayoutEntity:
        pass

    @abstractmethod
    async def get_payout_by_id(self, payout_id: int) -> Optional[PayoutEntity]:
        pass


@final
class PayoutRepository(PayoutBankDBRepository, PayoutRepositoryInterface):
    def __init__(self, database: DB):
        super().__init__(_database=database)

    async def create_payout(self, data: PayoutCreate) -> PayoutEntity:
        stmt = (
            payouts.table.insert()
            .values(data.dict(skip_defaults=True), created_at=datetime.utcnow())
            .returning(*payouts.table.columns.values())
        )
        row = await self._database.master().fetch_one(stmt)
        assert row is not None
        return PayoutEntity.from_row(row)

    async def get_payout_by_id(self, payout_id: int) -> Optional[PayoutEntity]:
        stmt = payouts.table.select().where(payouts.id == payout_id)
        row = await self._database.master().fetch_one(stmt)
        return PayoutEntity.from_row(row) if row else None
