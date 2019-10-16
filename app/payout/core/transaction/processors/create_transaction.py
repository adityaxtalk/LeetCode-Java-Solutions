from datetime import datetime

from structlog.stdlib import BoundLogger
from typing import Optional, Union

from app.commons.api.models import DEFAULT_INTERNAL_EXCEPTION, PaymentException
from app.commons.core.processor import AsyncOperation, OperationRequest
from app.payout.core.transaction.types import TransactionInternal
from app.payout.repository.bankdb.model.transaction import TransactionCreateDBEntity
from app.payout.repository.bankdb.transaction import TransactionRepositoryInterface


class CreateTransactionRequest(OperationRequest):
    amount: int
    amount_paid: int = 0  # same default behavior as DSJ
    payment_account_id: int
    idempotency_key: str
    currency: str
    target_id: int
    target_type: str
    transfer_id: Optional[int]
    created_at: Optional[datetime]
    created_by_id: Optional[int]
    notes: Optional[str]
    metadata: Optional[str]
    state: Optional[str]
    updated_at: Optional[datetime]
    dsj_id: Optional[int]
    payout_id: Optional[int]
    inserted_at: Optional[datetime]


class CreateTransaction(AsyncOperation[CreateTransactionRequest, TransactionInternal]):
    """
    Processor to create a transaction based on different parameters
    """

    transaction_repo: TransactionRepositoryInterface

    def __init__(
        self,
        request: CreateTransactionRequest,
        *,
        transaction_repo: TransactionRepositoryInterface,
        logger: BoundLogger = None
    ):
        super().__init__(request, logger)
        self.request = request
        self.transaction_repo = transaction_repo

    async def _execute(self) -> TransactionInternal:
        transaction_create_request_to_repo = TransactionCreateDBEntity(
            **self.request.dict()
        )
        transaction = await self.transaction_repo.create_transaction(
            data=transaction_create_request_to_repo
        )

        return TransactionInternal(
            **transaction.dict(), payout_account_id=transaction.payment_account_id
        )

    def _handle_exception(
        self, internal_exec: BaseException
    ) -> Union[PaymentException, TransactionInternal]:
        raise DEFAULT_INTERNAL_EXCEPTION
