import pytest

from app.commons.database.model import Database
from app.payout.repository.maindb.model.stripe_transfer import (
    StripeTransferCreate,
    StripeTransferUpdate,
)
from app.payout.repository.maindb.model.transfer import TransferCreate, TransferUpdate
from app.payout.repository.maindb.transfer import TransferRepository


class TestTransferRepository:
    pytestmark = [pytest.mark.asyncio]

    @pytest.fixture
    def transfer_repo(self, payout_maindb: Database) -> TransferRepository:
        return TransferRepository(database=payout_maindb)

    async def test_create_update_get_transfer(self, transfer_repo: TransferRepository):
        data = TransferCreate(
            subtotal=123, adjustments="some-adjustment", amount=123, method="stripe"
        )

        created = await transfer_repo.create_transfer(data)
        assert created.id, "account is created, assigned an ID"

        assert created == await transfer_repo.get_transfer_by_id(
            created.id
        ), "retrieved account matches"

        update_data = TransferUpdate(
            subtotal=123, adjustments="some-adjustment", amount=123, method="stripe"
        )

        updated = await transfer_repo.update_transfer_by_id(
            transfer_id=created.id, data=update_data
        )

        assert updated
        assert updated.subtotal == update_data.subtotal
        assert updated.adjustments == update_data.adjustments
        assert updated.amount == update_data.amount
        assert updated.method == update_data.method

    async def test_get_transfer_by_id_not_found(self, transfer_repo):
        assert not await transfer_repo.get_transfer_by_id(transfer_id=-1)

    async def test_update_transfer_by_id_not_found(self, transfer_repo):
        assert not await transfer_repo.update_transfer_by_id(
            transfer_id=-1, data=TransferUpdate(subtotal=100)
        )

    async def test_create_update_get_delete_stripe_transfer(self, transfer_repo):
        existing_transfer = await transfer_repo.create_transfer(
            TransferCreate(
                subtotal=123, adjustments="some-adjustment", amount=123, method="stripe"
            )
        )

        data = StripeTransferCreate(
            stripe_status="status", transfer_id=existing_transfer.id
        )

        created = await transfer_repo.create_stripe_transfer(data)
        assert created.id, "account is created, assigned an ID"

        assert created == await transfer_repo.get_stripe_transfer_by_id(
            created.id
        ), "retrieved account matches"

        assert created == await transfer_repo.get_stripe_transfer_by_stripe_id(
            stripe_id=created.stripe_id
        )

        assert created in await transfer_repo.get_stripe_transfers_by_transfer_id(
            transfer_id=created.transfer_id
        )

        update_data = StripeTransferUpdate(stripe_status="new_status")

        updated = await transfer_repo.update_stripe_transfer_by_id(
            stripe_transfer_id=created.id, data=update_data
        )

        assert updated
        assert updated.stripe_status == update_data.stripe_status
        assert updated.transfer_id == created.transfer_id

        await transfer_repo.delete_stripe_transfer_by_stripe_id(
            stripe_id=updated.stripe_id
        )

        assert not await transfer_repo.get_stripe_transfer_by_id(
            stripe_transfer_id=updated.transfer_id
        )

    async def test_get_stripe_transfer_by_id_not_found(self, transfer_repo):
        assert not await transfer_repo.get_stripe_transfer_by_id(stripe_transfer_id=-1)

    async def test_get_stripe_transfer_by_stripe_id_not_found(self, transfer_repo):
        assert not await transfer_repo.get_stripe_transfer_by_stripe_id(
            stripe_id="heregoesnothing"
        )

    async def test_get_stripe_transfer_by_transfer_id_not_found(self, transfer_repo):
        empty = await transfer_repo.get_stripe_transfers_by_transfer_id(transfer_id=-1)
        assert len(empty) == 0

    async def test_update_stripe_transfer_by_id_not_found(self, transfer_repo):
        assert not await transfer_repo.update_stripe_transfer_by_id(
            stripe_transfer_id=-1, data=StripeTransferUpdate(stripe_status="st")
        )

    async def test_delete_stripe_transfer_by_stripe_id_not_found(self, transfer_repo):
        await transfer_repo.delete_stripe_transfer_by_stripe_id(
            stripe_id="heregoesnothing"
        )
