import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import WalletNotFound
from api.schemas import WalletOperationsSchema, WalletOperationsEnum, WalletSchema
from api.service import WalletService
from database import get_db

api_router = APIRouter(prefix="/api/v1", tags=["Wallet"])


@api_router.get("/wallets/{uuid}", description="Accept uuid of wallet and returns wallet info.")
async def get_stats(
        uuid: str,
        session: AsyncSession = Depends(get_db)
):
    stats = await WalletService.get_one_or_none(session=session, uuid=uuid)
    if stats:
        return stats
    raise WalletNotFound


@api_router.post(
    "/wallets/{uuid}/operation",
    description="Accept uuid of wallet and make one operation(deposit or withdraw)."
)
async def wallet_operation(
        uuid: str,
        operation_data: WalletOperationsSchema,
        session: AsyncSession = Depends(get_db)
):
    operation = await WalletService.apply_wallet_operation(
        uuid=uuid,
        operation=operation_data,
        session=session
    )
    return operation


@api_router.post(
    "/wallets/create",
    description="Create a empty wallet and returns uuid.",
    response_model=WalletSchema
)
async def create_wallet(session: AsyncSession = Depends(get_db)) -> str:
    _generate_uuid = uuid.uuid4()
    new_wallet = await WalletService.create(
        session=session,
        uuid=str(_generate_uuid)
    )
    return new_wallet
