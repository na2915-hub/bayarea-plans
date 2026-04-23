from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid

TIME_WINDOWS = ["morning", "afternoon", "evening"]
VIBES        = ["chill", "social", "active", "adventurous"]
GROUP_STATUS = ["open", "confirmed", "closed"]

ACTIVITY_OPTIONS = [
    "hiking", "coffee", "brunch", "museums", "beach",
    "cycling", "yoga", "live music", "food tour", "picnic",
    "climbing", "wine bar", "bookstore", "farmer's market", "walk",
]


def normalize_text(value: str) -> str:
    return value.strip().lower()

def normalize_list(values: list[str]) -> list[str]:
    return [normalize_text(v) for v in values]


@dataclass
class User:
    name: str
    bio: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.name = normalize_text(self.name)
        if self.bio:
            self.bio = self.bio.strip()


@dataclass
class Plan:
    user_id: str
    user_name: str
    city: str
    date: date
    time_window: str
    activities: list[str]
    vibe: str
    max_group_size: int = 4                              # 2–6, default 4
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.city        = normalize_text(self.city)
        self.time_window = normalize_text(self.time_window)
        self.vibe        = normalize_text(self.vibe)
        self.activities  = normalize_list(self.activities)


@dataclass
class Group:
    plan_id: str
    member_ids: list[str] = field(default_factory=list)
    status: str = "open"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
