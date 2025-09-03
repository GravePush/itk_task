import asyncio

import pytest
from httpx import AsyncClient

from api.schemas import WalletOperationsSchema
from api.service import WalletService


async def get_wallet_stats(uuid: str, ac: AsyncClient):
    response = await ac.get(f"api/v1/wallets/{uuid}")
    return response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uuid, balance, expected_result", [
        ("f47ac10b-58cc-4372-a567-0e02b2c3d479", 1000, 200),
        ("11111111-1111-1111-1111-111111111111", 1, 404),
        ("abc", 1, 404),
    ]
)
async def test_get_stats(
        uuid: str,
        expected_result: int,
        balance: int,
        ac: AsyncClient
):
    response = await get_wallet_stats(uuid=uuid, ac=ac)
    json_response = response.json()

    assert response.status_code == expected_result

    if expected_result == 200:
        assert json_response["uuid"] == uuid
        assert json_response["balance"] == balance
    if expected_result == 404:
        assert json_response["detail"] == "Wallet not found!"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uuid, payload, expected_status", [
        (
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                {"operation_type": "DEPOSIT", "amount": 1000},
                200
        ),
        (
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                {"operation_type": "WITHDRAW", "amount": 1000},
                200
        ),
        (
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                {"operation_type": "WITHDRAW", "amount": 1001},
                400
        ),
        (
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                {"operation_type": "invalid command", "amount": 100},
                422
        ),
        (
                "123",
                {"operation_type": "DEPOSIT", "amount": 1000},
                404
        ),
    ]
)
async def test_wallet_operation(
        uuid: str,
        payload: dict,
        expected_status: int,
        ac: AsyncClient
):
    balance_before = await get_wallet_stats(uuid=uuid, ac=ac)
    balance_before = balance_before.json()
    response = await ac.post(f"api/v1/wallets/{uuid}/operation", json=payload)
    balance_after = await get_wallet_stats(uuid=uuid, ac=ac)
    balance_after = balance_after.json()

    assert response.status_code == expected_status

    if expected_status == 200 and payload["operation_type"] == "DEPOSIT":
        calculated_amount = balance_after["balance"] - balance_before["balance"]
        assert calculated_amount == payload["amount"]
    if expected_status == 200 and payload["operation_type"] == "WITHDRAW":
        calculated_amount = balance_before["balance"] - balance_after["balance"]
        assert calculated_amount == payload["amount"]


# Результаты этого теста недетерминированы: при конкурентных операциях возможны 200/400/409
# в зависимости от порядка блокировок, что является ожидаемым поведением.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uuid, payload_1, payload_2, expected_codes", [
        (
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",  # <- balance 1000
                {"operation_type": "WITHDRAW", "amount": 1000},
                {"operation_type": "WITHDRAW", "amount": 500},
                [200, 400]
        ),
        (
                "9c858901-8a57-4791-81fe-4c455b099bc9",  # <- balance 1000
                {"operation_type": "WITHDRAW", "amount": 500},
                {"operation_type": "WITHDRAW", "amount": 500},
                [200, 200]
        ),
        (
                "16fd2706-8baf-433b-82eb-8c7fada847da",  # <- balance 1000
                {"operation_type": "WITHDRAW", "amount": 10000},
                {"operation_type": "WITHDRAW", "amount": 500},
                [400, 409]
        ),

    ]
)
async def test_concurrent_withdraw(
        uuid: str,
        payload_1: dict,
        payload_2: dict,
        expected_codes: list,
        session_for_concurrent_withdraw,
        ac: AsyncClient
):
    operation_1 = WalletOperationsSchema(**payload_1)
    operation_2 = WalletOperationsSchema(**payload_2)

    async with session_for_concurrent_withdraw() as session1, session_for_concurrent_withdraw() as session2:
        results = await asyncio.gather(
            WalletService.apply_wallet_operation(uuid, operation_1, session1),
            WalletService.apply_wallet_operation(uuid, operation_2, session2),
            return_exceptions=True
        )

    wallet_1 = await get_wallet_stats(uuid="f47ac10b-58cc-4372-a567-0e02b2c3d479", ac=ac)
    wallet_2 = await get_wallet_stats(uuid="9c858901-8a57-4791-81fe-4c455b099bc9", ac=ac)
    wallet_3 = await get_wallet_stats(uuid="16fd2706-8baf-433b-82eb-8c7fada847da", ac=ac)

    json_wallet_1 = wallet_1.json()
    json_wallet_2 = wallet_2.json()
    json_wallet_3 = wallet_3.json()

    assert json_wallet_1["balance"] >= 0
    assert json_wallet_2["balance"] >= 0
    assert json_wallet_3["balance"] >= 0

    actual_codes = []
    for r in results:
        if isinstance(r, Exception):
            actual_codes.append(r.status_code if hasattr(r, "status_code") else None)
        else:
            actual_codes.append(200)
    assert actual_codes == expected_codes
