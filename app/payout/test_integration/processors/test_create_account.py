import asyncio

import pytest
import pytest_mock
from IPython.utils.tz import utcnow

from app.payout.core.account.processors.create_account import (
    CreatePayoutAccount,
    CreatePayoutAccountRequest,
)
from app.payout.core.account import models as account_models
from app.payout.repository.maindb.model.payment_account import PaymentAccount
from app.payout.repository.maindb.payment_account import PaymentAccountRepository
from app.payout.models import PayoutAccountTargetType


class TestCreatePayoutAccount:
    pytestmark = [pytest.mark.asyncio]

    async def test_create_payout_account(
        self,
        mocker: pytest_mock.MockFixture,
        payment_account_repo: PaymentAccountRepository,
    ):
        request = CreatePayoutAccountRequest(
            entity=PayoutAccountTargetType.DASHER,
            statement_descriptor="test_create_account_processor",
        )
        payment_account = PaymentAccount(
            id=1,
            created_at=utcnow(),
            statement_descriptor="test_create_account_processor",
        )

        create_account_op = CreatePayoutAccount(
            logger=mocker.Mock(),
            payment_account_repo=payment_account_repo,
            request=request,
        )

        @asyncio.coroutine
        def mock_create_payment_account(*args):
            return payment_account

        mocker.patch(
            "app.payout.repository.maindb.payment_account.PaymentAccountRepository.create_payment_account",
            side_effect=mock_create_payment_account,
        )
        created_payout_account: account_models.PayoutAccountInternal = await create_account_op._execute()
        assert created_payout_account.payment_account.id == 1
        assert (
            created_payout_account.payment_account.statement_descriptor
            == "test_create_account_processor"
        )