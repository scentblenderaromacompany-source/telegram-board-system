"""
Health check and status dashboard.
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class HealthCheck:
    name: str
    status: str = "unknown"
    message: str = ""
    latency_ms: float = 0
    last_checked: float = 0
    details: Dict[str, Any] = field(default_factory=dict)

class HealthDashboard:
    """
    System health monitoring dashboard.
    """
    
    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._start_time = time.time()
    
    def register_check(self, name: str, check_func):
        self._checks[name] = HealthCheck(name=name)
        self._check_funcs = getattr(self, "_check_funcs", {})
        self._check_funcs[name] = check_func
    
    async def run_checks(self, integration=None) -> Dict[str, Any]:
        results = {}
        
        results["system"] = {
            "status": "healthy",
            "uptime_seconds": time.time() - self._start_time,
            "timestamp": time.time(),
        }
        
        if integration:
            metrics = integration.get_metrics()
            results["bots"] = {}
            for bot_id, bot_metrics in metrics.get("bots", {}).items():
                results["bots"][bot_id] = {
                    "status": "healthy" if bot_metrics.get("errors", 0) < 10 else "degraded",
                    "messages_received": bot_metrics.get("messages_received", 0),
                    "messages_sent": bot_metrics.get("messages_sent", 0),
                    "errors": bot_metrics.get("errors", 0),
                }
            
            results["agents"] = {
                "total": len(metrics.get("agents", {})),
                "running": sum(1 for a in metrics.get("agents", {}).values() if a.get("state") == "running"),
            }
            
            results["memory"] = metrics.get("memory", {})
        
        for name, check in self._checks.items():
            try:
                if name in self._check_funcs:
                    start = time.time()
                    result = await self._check_funcs[name]()
                    latency = (time.time() - start) * 1000
                    check.status = "healthy"
                    check.latency_ms = latency
                    check.last_checked = time.time()
                    check.details = result if isinstance(result, dict) else {}
                    results[name] = {"status": "healthy", "latency_ms": latency}
            except Exception as e:
                check.status = "unhealthy"
                check.message = str(e)
                results[name] = {"status": "unhealthy", "error": str(e)}
        
        all_healthy = all(r.get("status") == "healthy" for r in results.values())
        results["overall"] = "healthy" if all_healthy else "degraded"
        
        return results
    
    def get_status_summary(self) -> str:
        lines = ["=== Health Status ===", ""]
        for name, check in self._checks.items():
            status_icon = "✅" if check.status == "healthy" else "❌" if check.status == "unhealthy" else "❓"
            lines.append(f"{status_icon} {name}: {check.status} ({check.latency_ms:.1f}ms)")
        return "\n".join(lines)
