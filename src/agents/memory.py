"""
Long-term memory store for agents.
"""
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryCategory(Enum):
    USER_PREFERENCE = "user_preference"
    BUSINESS_CONTEXT = "business_context"
    LEARNED_BEHAVIOR = "learned_behavior"
    PROJECT_HISTORY = "project_history"
    RELATIONSHIP = "relationship"
    SKILL_KNOWLEDGE = "skill_knowledge"
    SOP_REFERENCE = "sop_reference"


@dataclass
class MemoryEntry:
    content: str
    category: Optional[MemoryCategory] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


class MemoryStore:
    def __init__(self, state_file: str = "config/memory.json", max_entries: int = 10000):
        self._entries: List[MemoryEntry] = []
        self._state_file = Path(state_file)
        self._max_entries = max_entries
        self._load()

    def _load(self):
        if self._state_file.exists():
            data = json.loads(self._state_file.read_text())
            for entry_data in data.get("entries", []):
                if "category" in entry_data and entry_data["category"]:
                    entry_data["category"] = MemoryCategory(entry_data["category"])
                self._entries.append(MemoryEntry(**entry_data))

    def _save(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": []}
        for entry in self._entries[-self._max_entries:]:
            d = {
                "content": entry.content,
                "category": entry.category.value if entry.category else None,
                "metadata": entry.metadata,
                "importance": entry.importance,
                "timestamp": entry.timestamp,
                "tags": entry.tags,
            }
            data["entries"].append(d)
        self._state_file.write_text(json.dumps(data, indent=2))

    async def store(self, entry: MemoryEntry):
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        self._save()

    def search(self, query: str, category: Optional[MemoryCategory] = None, limit: int = 10) -> List[MemoryEntry]:
        results = []
        query_lower = query.lower()
        for entry in reversed(self._entries):
            if category and entry.category != category:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        return sorted(results, key=lambda e: (-e.importance, -e.timestamp))

    def get_recent(self, limit: int = 20) -> List[MemoryEntry]:
        return list(reversed(self._entries[-limit:]))

    def get_by_category(self, category: MemoryCategory, limit: int = 50) -> List[MemoryEntry]:
        return [e for e in self._entries if e.category == category][-limit:]

    def delete(self, content: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.content != content]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def get_stats(self) -> Dict:
        categories = {}
        for entry in self._entries:
            cat = entry.category.value if entry.category else "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        return {"total_entries": len(self._entries), "categories": categories}
