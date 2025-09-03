from enum import Enum
from pydantic import BaseModel, field_validator, Field


class WalletOperationsEnum(str, Enum):
    deposit = "DEPOSIT"
    withdraw = "WITHDRAW"


class WalletSchema(BaseModel):
    uuid: str


class WalletOperationsSchema(BaseModel):
    operation_type: WalletOperationsEnum
    amount: int = Field(ge=0)

    @field_validator("operation_type", mode="before")
    @classmethod
    def validate_case(cls, value: str):
        if isinstance(value, str):
            return value.upper()

        return value
