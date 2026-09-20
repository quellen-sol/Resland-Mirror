from pydantic import BaseModel


class AdminUserRow(BaseModel):
    auth0_id: str
    email: str | None
    full_name: str | None
    token_balance: int
    credits_used: int
    input_tokens: int
    output_tokens: int
    credits_purchased: int


class AdminUsersResponse(BaseModel):
    users: list[AdminUserRow]


class UsageByModelRow(BaseModel):
    model: str
    job_count: int
    input_tokens: int
    output_tokens: int
    credits: int


class UsageByKindRow(BaseModel):
    job_kind: str
    job_count: int
    credits: int


class UsageByDayRow(BaseModel):
    day: str
    credits: int


class RecentUsageRow(BaseModel):
    id: int
    user_id: str
    job_kind: str
    job_id: str
    model: str
    input_tokens: int
    output_tokens: int
    credits_charged: int
    created_at: str


class AdminUsageResponse(BaseModel):
    by_model: list[UsageByModelRow]
    by_kind: list[UsageByKindRow]
    by_day: list[UsageByDayRow]
    recent: list[RecentUsageRow]


class AdminPurchaseRow(BaseModel):
    id: str
    user_id: str
    credits: int
    amount_cents: int
    currency: str
    status: str
    created_at: str


class AdminPurchasesResponse(BaseModel):
    revenue_cents: int
    purchases: list[AdminPurchaseRow]
