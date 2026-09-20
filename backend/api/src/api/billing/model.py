from pydantic import BaseModel


class TokenPack(BaseModel):
    id: str
    name: str
    credits: int
    amount_cents: int
    currency: str


# Server-side pack catalog — the client sends only `id`, so price and credit
# amounts can never be tampered with.
TOKEN_PACKS: dict[str, TokenPack] = {
    "starter": TokenPack(
        id="starter",
        name="Starter — 500K tokens",
        credits=500_000,
        amount_cents=500,
        currency="usd",
    ),
    "standard": TokenPack(
        id="standard",
        name="Standard — 1.1M tokens",
        credits=1_100_000,
        amount_cents=1000,
        currency="usd",
    ),
    "pro": TokenPack(
        id="pro",
        name="Pro — 2.5M tokens",
        credits=2_500_000,
        amount_cents=2000,
        currency="usd",
    ),
}


class CheckoutRequest(BaseModel):
    pack_id: str


class CheckoutResponse(BaseModel):
    url: str


class BalanceResponse(BaseModel):
    token_balance: int


class PurchaseItem(BaseModel):
    id: str
    credits: int
    amount_cents: int
    currency: str
    status: str
    created_at: str


class PurchasesResponse(BaseModel):
    purchases: list[PurchaseItem]


class ModelInfo(BaseModel):
    id: str
    display_name: str
    credits_per_1k_input: int
    credits_per_1k_output: int


class ModelsResponse(BaseModel):
    models: list[ModelInfo]
