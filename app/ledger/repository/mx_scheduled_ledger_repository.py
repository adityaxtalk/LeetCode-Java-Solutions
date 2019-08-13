from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pytz import timezone
from math import ceil
from typing import Optional

from sqlalchemy import and_

from app.ledger.core.mx_transaction.data_types import (
    InsertMxScheduledLedgerInput,
    InsertMxScheduledLedgerOutput,
    GetMxScheduledLedgerByLedgerInput,
    GetMxScheduledLedgerByLedgerOutput,
    GetMxScheduledLedgerInput,
    GetMxScheduledLedgerOutput,
)
from app.ledger.core.mx_transaction.types import (
    MxScheduledLedgerIntervalType,
    MxLedgerStateType,
)
from app.ledger.models.paymentdb import mx_scheduled_ledgers, mx_ledgers
from app.ledger.repository.base import LedgerDBRepository


class MxScheduledLedgerRepositoryInterface:
    @abstractmethod
    async def insert_mx_scheduled_ledger(
        self, request: InsertMxScheduledLedgerInput
    ) -> InsertMxScheduledLedgerOutput:
        ...

    @abstractmethod
    async def get_mx_scheduled_ledger_by_ledger_id(
        self, request: GetMxScheduledLedgerByLedgerInput
    ) -> Optional[GetMxScheduledLedgerByLedgerOutput]:
        ...

    @abstractmethod
    async def get_open_mx_scheduled_ledger_for_period(
        self, request: GetMxScheduledLedgerInput
    ) -> Optional[GetMxScheduledLedgerOutput]:
        ...


@dataclass
class MxScheduledLedgerRepository(
    MxScheduledLedgerRepositoryInterface, LedgerDBRepository
):
    async def insert_mx_scheduled_ledger(
        self, request: InsertMxScheduledLedgerInput
    ) -> InsertMxScheduledLedgerOutput:
        stmt = (
            mx_scheduled_ledgers.table.insert()
            .values(request.dict(skip_defaults=True))
            .returning(*mx_scheduled_ledgers.table.columns.values())
        )
        row = await self.payment_database.master().fetch_one(stmt)
        assert row
        return InsertMxScheduledLedgerOutput.from_row(row)

    async def get_mx_scheduled_ledger_by_ledger_id(
        self, request: GetMxScheduledLedgerByLedgerInput
    ) -> Optional[GetMxScheduledLedgerByLedgerOutput]:
        stmt = mx_scheduled_ledgers.table.select().where(
            mx_scheduled_ledgers.ledger_id == request.id
        )
        row = await self.payment_database.master().fetch_one(stmt)
        # if no result found, return nothing
        if not row:
            return None
        return GetMxScheduledLedgerByLedgerOutput.from_row(row)

    async def get_open_mx_scheduled_ledger_for_period(
        self, request: GetMxScheduledLedgerInput
    ) -> Optional[GetMxScheduledLedgerOutput]:
        """
        Get mx_scheduled_ledger with given payment_account_id, routing_key, interval_type and corresponding open mx ledger
        :param request: GetMxScheduledLedgerInput
        :return: GetMxScheduledLedgerOutput
        """
        stmt = mx_scheduled_ledgers.table.select().where(
            and_(
                mx_scheduled_ledgers.payment_account_id
                == request.payment_account_id,  # noqa: W503
                mx_scheduled_ledgers.start_time
                == self.pacific_start_time_for_current_interval(  # noqa: W503
                    request.routing_key, request.interval_type
                ),
                mx_ledgers.state == MxLedgerStateType.OPEN,
                mx_ledgers.table.c.id == mx_scheduled_ledgers.ledger_id,
            )
        )
        row = await self.payment_database.master().fetch_one(stmt)
        if not row:
            return None
        return GetMxScheduledLedgerOutput.from_row(row)

    def pacific_start_time_for_current_interval(
        self, routing_key: datetime, interval: Optional[MxScheduledLedgerIntervalType]
    ) -> datetime:
        """
        Calculate the start_time(in UTC time but without tz info) for current interval based on given routing_key and interval
        The returned start_time represents Pacific start_time in UTC timezone
        :param routing_key: datetime, key to find the cur start_time
        :param interval: MxScheduledLedgerIntervalType,
        :return: start_time for current interval: datetime
        """
        interval_in_timedelta = (
            timedelta(days=7)
            if interval == MxScheduledLedgerIntervalType.WEEKLY
            else timedelta(days=1)
        )
        routing_key_utc = routing_key.astimezone(timezone("UTC"))
        base_timestamp = timezone("US/Pacific").localize(datetime(2019, 7, 1))
        num_intervals = ceil((routing_key_utc - base_timestamp) / interval_in_timedelta)
        start_time = base_timestamp + interval_in_timedelta * (num_intervals - 1)
        return start_time.astimezone(timezone("UTC")).replace(tzinfo=None)

    def pacific_end_time_for_current_interval(
        self, routing_key: datetime, interval: Optional[MxScheduledLedgerIntervalType]
    ) -> datetime:
        interval_in_timedelta = (
            timedelta(days=7)
            if interval == MxScheduledLedgerIntervalType.WEEKLY
            else timedelta(days=1)
        )
        routing_key_utc = routing_key.astimezone(timezone("UTC"))
        base_timestamp = timezone("US/Pacific").localize(datetime(2019, 7, 1))
        num_intervals = ceil((routing_key_utc - base_timestamp) / interval_in_timedelta)
        start_time = base_timestamp + interval_in_timedelta * num_intervals
        return start_time.astimezone(timezone("UTC")).replace(tzinfo=None)