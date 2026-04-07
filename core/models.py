from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(eq=False)
class ProfileRecord:
    """Immutable-by-convention record for a single Instagram profile entry."""

    username: str
    profile_url: str
    timestamp: Optional[datetime]
    source_file: str

    def __hash__(self) -> int:
        return hash(self.username.lower())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProfileRecord):
            return NotImplemented
        return self.username.lower() == other.username.lower()


@dataclass
class AnalysisResult:
    """Container for the full output of the analytics engine."""

    followers: list[ProfileRecord] = field(default_factory=list)
    following: list[ProfileRecord] = field(default_factory=list)
    not_following_back: list[ProfileRecord] = field(default_factory=list)
    fans: list[ProfileRecord] = field(default_factory=list)
    mutual: list[ProfileRecord] = field(default_factory=list)
    blocked: list[ProfileRecord] = field(default_factory=list)
    recently_unfollowed: list[ProfileRecord] = field(default_factory=list)
    skipped_entries: int = 0

    @property
    def follower_count(self) -> int:
        return len(self.followers)

    @property
    def following_count(self) -> int:
        return len(self.following)

    @property
    def ratio(self) -> float:
        if self.following_count == 0:
            return 0.0
        return round(self.follower_count / self.following_count, 2)
