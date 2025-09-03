from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import WalletNotFound, InsufficientBalance, ConcurrencyException
from api.models import WalletModel
from api.schemas import WalletOperationsSchema, WalletOperationsEnum
from base_services.base_service import BaseService


class WalletService(BaseService):
    model = WalletModel

    @classmethod
    async def apply_wallet_operation(
            cls,
            uuid: str,
            operation: WalletOperationsSchema,
            session: AsyncSession
    ):
        try:
            wallet = await cls.get_one_or_none(session=session, uuid=uuid, to_update=True, no_wait=True)
            if wallet:
                if operation.operation_type == WalletOperationsEnum.deposit:
                    wallet.balance += operation.amount
                if operation.operation_type == WalletOperationsEnum.withdraw:
                    if wallet.balance < operation.amount:
                        raise InsufficientBalance

                    wallet.balance -= operation.amount

                await session.commit()
                await session.refresh(wallet)

                return wallet

            raise WalletNotFound
        except DBAPIError:
            raise ConcurrencyException
