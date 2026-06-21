"""
Metrics collection and health checking.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """
    Collects and aggregates metrics across the system.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        point = MetricPoint(name=name, value=value, tags=tags or {})
        self._metrics[name].append(point)
        if len(self._metrics[name]) > 10000:
            self._metrics[name] = self._metrics[name][-5000:]
    
    def increment(self, name: str, amount: int = 1):
        self._counters[name] += amount
    
    def set_gauge(self, name: str, value: float):
        self._gauges[name] = value
    
    def observe_histogram(self, name: str, value: float):
        self._histograms[name].append(value)
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-500:]
    
    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict:
        values = self._histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        sorted_vals = sorted(values)
        return {
            "count": len(values),
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "avg": sum(values) / len(values),
            "p50": sorted_vals[len(sorted_vals) // 2],
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
            "p99": sorted_vals[int(len(sorted_vals) * 0.99)],
        }
    
    def get_all(self) -> Dict:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: self.get_histogram_stats(k) for k in self._histograms},
        }
    
    def reset(self):
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


class HealthChecker:
    """
    System health checking with configurable checks.
    """
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._results: Dict[str, Dict] = {}
    
    def register_check(self, name: str, check_func: callable):
        self._checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Dict]:
        for name, check_func in self._checks.items():
            try:
                result = await check_func()
                self._results[name] = {"status": "healthy", "details": result}
            except Exception as e:
                self._results[name] = {"status": "unhealthy", "error": str(e)}
        return self._results
    
    def get_status(self) -> str:
        if not self._results:
            return "unknown"
        unhealthy = [k for k, v in self._results.items() if v["status"] != "healthy"]
        if unhealthy:
            return "degraded"
        return "healthy"
    
    def get_report(self) -> Dict:
        return {
            "overall": self.get_status(),
            "checks": self._results,
            "total_checks": len(self._checks),
            "healthy": sum(1 for v in self._results.values() if v["status"] == "healthy"),
            "unhealthy": sum(1 for v in self._results.values() if v["status"] != "healthy"),
        }
