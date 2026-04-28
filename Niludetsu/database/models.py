from __future__ import annotations

from typing import TypedDict, Optional


class UserRow(TypedDict, total=False):
    user_id: str
    guild_id: str
    created_at: str


class UserEconomyRow(TypedDict, total=False):
    user_id: str
    guild_id: str
    balance: int
    deposit: int
    spousal_balance: int
    spousal_enabled: bool
    cooldowns: dict[str, str]


class UserProfileRow(TypedDict, total=False):
    user_id: str
    guild_id: str
    level: int
    experience: int
    reputation: int


class UserAnalyticsRow(TypedDict, total=False):
    guild_id: str
    user_id: str
    messages_total: int
    messages_deleted: int
    voice_seconds: int
    message_channels: dict[str, int]
    voice_channels: dict[str, int]
    last_voice_join: Optional[str]
    last_updated: str


class UserBundle(TypedDict):
    core: UserRow
    economy: UserEconomyRow
    profile: UserProfileRow
    analytics: UserAnalyticsRow
    marriage: Optional[dict]


class UserQuestRow(TypedDict, total=False):
    id: int
    user_id: str
    guild_id: str
    quest_key: str
    progress: int
    target: int
    reward: int
    quest_type: str
    expires_at: str
    claimed: bool


class UserInventoryRow(TypedDict, total=False):
    id: int
    user_id: str
    guild_id: str
    item_type: str
    item_key: str
    quantity: int
    metadata: dict


class UserTransactionRow(TypedDict, total=False):
    id: int
    user_id: str
    guild_id: str
    event: str
    amount: int
    balance_after: int
    related_user_id: Optional[str]
    metadata: dict
    created_at: str


class UserMarriageRow(TypedDict, total=False):
    id: int
    guild_id: str
    partner_a_id: str
    partner_b_id: str
    status: str
    metadata: dict
    created_at: str


class UserRudimentRow(TypedDict, total=False):
    id: int
    guild_id: str
    user_id: str
    moderator_id: str
    action_type: str
    reason: str
    active: bool
    expires_at: Optional[str]
    rudiment: str
    created_at: str


class UserAchievementRow(TypedDict, total=False):
    id: int
    guild_id: str
    user_id: str
    achievement_id: str
    unlocked_at: str


class RoleRow(TypedDict, total=False):
    id: int
    guild_id: str
    role_id: str
    name: str
    price: int
    owner_id: Optional[str]


class SettingsRow(TypedDict):
    key: str
    value: dict | list | str | int | float | bool
    updated_at: str
