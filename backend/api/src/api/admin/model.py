from pydantic import BaseModel


class AdminUserRow(BaseModel):
    auth0_id: str
    email: str | None
    full_name: str | None
    balance_cents: float
    cents_used: float
    input_tokens: int
    output_tokens: int
    cents_purchased: int


class AdminUsersResponse(BaseModel):
    users: list[AdminUserRow]


class UsageByModelRow(BaseModel):
    model: str
    job_count: int
    input_tokens: int
    output_tokens: int
    cents: float


class UsageByKindRow(BaseModel):
    job_kind: str
    job_count: int
    cents: float


class UsageByDayRow(BaseModel):
    day: str
    cents: float


class RecentUsageRow(BaseModel):
    id: int
    user_id: str
    job_kind: str
    job_id: str
    model: str
    input_tokens: int
    output_tokens: int
    amount_cents: float
    actual_cost_cents: float | None
    created_at: str


class AdminUsageResponse(BaseModel):
    by_model: list[UsageByModelRow]
    by_kind: list[UsageByKindRow]
    by_day: list[UsageByDayRow]
    recent: list[RecentUsageRow]


class ModelPricingRow(BaseModel):
    id: str
    display_name: str
    cents_per_1k_input: float
    cents_per_1k_output: float
    enabled: bool
    is_default: bool
    sort_order: int


class AdminModelsResponse(BaseModel):
    models: list[ModelPricingRow]


class ModelPricingUpsert(BaseModel):
    display_name: str
    cents_per_1k_input: float
    cents_per_1k_output: float
    enabled: bool
    is_default: bool
    sort_order: int


class AdminPurchaseRow(BaseModel):
    id: str
    user_id: str
    cents: int
    amount_cents: int
    currency: str
    status: str
    created_at: str


class AdminPurchasesResponse(BaseModel):
    revenue_cents: int
    purchases: list[AdminPurchaseRow]
