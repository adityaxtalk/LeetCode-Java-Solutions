from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from typing_extensions import final

from app.commons.database.infra import DB
from app.payout.repository.bankdb.base import PayoutBankDBRepository
from app.payout.repository.bankdb.model import stripe_payout_requests
from app.payout.repository.bankdb.model.stripe_payout_request import (
    StripePayoutRequestEntity,
    StripePayoutRequestCreate,
)


class StripePayoutRequestRepositoryInterface(ABC):
    @abstractmethod
    async def create_stripe_payout_request(
        self, data: StripePayoutRequestCreate
    ) -> StripePayoutRequestEntity:
        pass

    @abstractmethod
    async def get_stripe_payout_request_by_payout_id(
        self, payout_id: int
    ) -> Optional[StripePayoutRequestEntity]:
        pass


@final
class StripePayoutRequestRepository(
    PayoutBankDBRepository, StripePayoutRequestRepositoryInterface
):
    def __init__(self, database: DB):
        super().__init__(_database=database)

    async def create_stripe_payout_request(
        self, data: StripePayoutRequestCreate
    ) -> StripePayoutRequestEntity:
        stmt = (
            stripe_payout_requests.table.insert()
            .values(data.dict(skip_defaults=True), created_at=datetime.utcnow())
            .returning(*stripe_payout_requests.table.columns.values())
        )
        row = await self._database.master().fetch_one(stmt)
        assert row is not None
        return StripePayoutRequestEntity.from_row(row)

    async def get_stripe_payout_request_by_payout_id(
        self, payout_id: int
    ) -> Optional[StripePayoutRequestEntity]:
        stmt = stripe_payout_requests.table.select().where(
            stripe_payout_requests.payout_id == payout_id
        )
        rows = await self._database.master().fetch_all(stmt)
        if rows:
            # since we have one-to-one mapping to payout
            assert len(rows) == 1
            return StripePayoutRequestEntity.from_row(rows[0])

        return None
