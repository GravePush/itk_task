from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class WalletModel(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
