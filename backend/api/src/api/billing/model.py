from pydantic import BaseModel


class TokenPack(BaseModel):
    id: str
    name: str
    cents: int
    amount_cents: int
    currency: str


# Server-side pack catalog — the client sends only `id`, so price and grant
# amounts can never be tampered with. `cents` is balance added, `amount_cents`
# is the Stripe charge; the difference is the bulk bonus.
TOKEN_PACKS: dict[str, TokenPack] = {
    "starter": TokenPack(
        id="starter",
        name="Starter",
        cents=500,
        amount_cents=500,
        currency="usd",
    ),
    "standard": TokenPack(
        id="standard",
        name="Standard",
        cents=1100,
        amount_cents=1000,
        currency="usd",
    ),
    "pro": TokenPack(
        id="pro",
        name="Pro",
        cents=2500,
        amount_cents=2000,
        currency="usd",
    ),
}


class CheckoutRequest(BaseModel):
    pack_id: str


class CheckoutResponse(BaseModel):
    url: str


class BalanceResponse(BaseModel):
    balance_cents: float


class PurchaseItem(BaseModel):
    id: str
    cents: int
    amount_cents: int
    currency: str
    status: str
    created_at: str


class PurchasesResponse(BaseModel):
    purchases: list[PurchaseItem]


class ModelInfo(BaseModel):
    id: str
    display_name: str
    cents_per_1k_input: float
    cents_per_1k_output: float


class ModelsResponse(BaseModel):
    models: list[ModelInfo]
