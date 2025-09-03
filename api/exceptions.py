from fastapi import HTTPException, status


class WalletExceptions(HTTPException):
    def __init__(self, detail: str, status_code: status):
        super().__init__(detail=detail, status_code=status_code)


class WalletNotFound(WalletExceptions):
    def __init__(self):
        super().__init__(
            detail="Wallet not found!",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InsufficientBalance(WalletExceptions):
    def __init__(self):
        super().__init__(
            detail="Insufficient balance!",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConcurrencyException(WalletExceptions):
    def __init__(self):
        super().__init__(
            detail="Resource busy, try again!",
            status_code=status.HTTP_409_CONFLICT
        )
