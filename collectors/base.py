from abc import ABC, abstractmethod
from typing import List, Dict


class Collector(ABC):
    """Base class for news collectors."""
    
    source_name: str
    
    @abstractmethod
    def fetch_items(self) -> List[Dict]:
        """Fetch news items and return list of dicts with keys: title, url, published_at, source."""
        pass
