import time
import os
import threading
from typing import Dict, List, Tuple, Any

START_TIME = time.time()

class PrometheusMetricsRegistry:
    """
    Thread-safe in-memory metrics registry outputting standard Prometheus text exposition format (v0.0.4).
    Zero external heavy dependencies required.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._gauges: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._histograms: Dict[str, Dict[Tuple[Tuple[str, str], ...], List[float]]] = {}
        self._help: Dict[str, str] = {}
        self._types: Dict[str, str] = {}

    def register_counter(self, name: str, help_text: str):
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
                self._help[name] = help_text
                self._types[name] = "counter"

    def register_gauge(self, name: str, help_text: str):
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
                self._help[name] = help_text
                self._types[name] = "gauge"

    def inc_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
                self._types[name] = "counter"
            self._counters[name][label_key] = self._counters[name].get(label_key, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        label_key = tuple(sorted((labels or {}).items()))
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
                self._types[name] = "gauge"
            self._gauges[name][label_key] = value

    def generate_metrics_text(self) -> str:
        lines = []
        now = time.time()
        
        # Update dynamic process gauges
        self.set_gauge("process_uptime_seconds", round(now - START_TIME, 2))
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On macOS ru_maxrss is bytes, on Linux it is KB
            mem_bytes = usage if "darwin" in os.sys.platform else usage * 1024
            self.set_gauge("process_resident_memory_bytes", float(mem_bytes))
        except Exception:
            pass

        with self._lock:
            # Format counters
            for name, series in sorted(self._counters.items()):
                help_str = self._help.get(name, f"Counter metric {name}")
                lines.append(f"# HELP {name} {help_str}")
                lines.append(f"# TYPE {name} counter")
                for label_key, val in sorted(series.items()):
                    lbl_str = self._format_labels(label_key)
                    lines.append(f"{name}{lbl_str} {val}")

            # Format gauges
            for name, series in sorted(self._gauges.items()):
                help_str = self._help.get(name, f"Gauge metric {name}")
                lines.append(f"# HELP {name} {help_str}")
                lines.append(f"# TYPE {name} gauge")
                for label_key, val in sorted(series.items()):
                    lbl_str = self._format_labels(label_key)
                    lines.append(f"{name}{lbl_str} {val}")

        return "\n".join(lines) + "\n"

    def _format_labels(self, label_key: Tuple[Tuple[str, str], ...]) -> str:
        if not label_key:
            return ""
        parts = [f'{k}="{v}"' for k, v in label_key]
        return "{" + ",".join(parts) + "}"


# Global Singleton
metrics_registry = PrometheusMetricsRegistry()

# Initialize core SaaS metrics
metrics_registry.register_counter("http_requests_total", "Total count of HTTP requests handled.")
metrics_registry.register_counter("rag_queries_total", "Total count of RAG queries processed.")
metrics_registry.register_counter("rag_injections_blocked_total", "Total prompt injection attacks blocked.")
metrics_registry.register_counter("rag_evidence_validations_total", "Evidence validation passes and rejections.")
metrics_registry.register_gauge("process_uptime_seconds", "Application process uptime in seconds.")
metrics_registry.register_gauge("process_resident_memory_bytes", "Resident process memory in bytes.")
metrics_registry.register_gauge("rag_indexed_documents_total", "Active documents indexed in knowledge base.")

def record_http_request(method: str, path: str, status_code: int):
    # Normalize path to prevent high label cardinality
    clean_path = path
    if path.startswith("/api/v1/documents/") and path.endswith("/status"):
        clean_path = "/api/v1/documents/:id/status"
    elif path.startswith("/api/v1/conversations/") and path.endswith("/messages"):
        clean_path = "/api/v1/conversations/:id/messages"
    elif path.startswith("/api/v1/admin/documents/"):
        clean_path = "/api/v1/admin/documents/:id"
    elif path.startswith("/api/v1/admin/users/"):
        clean_path = "/api/v1/admin/users/:id/role"
        
    metrics_registry.inc_counter(
        "http_requests_total",
        labels={"method": method, "path": clean_path, "status": str(status_code)}
    )

def record_rag_query(language: str, is_fallback: bool):
    metrics_registry.inc_counter(
        "rag_queries_total",
        labels={"language": str(language or "unknown"), "fallback": str(is_fallback).lower()}
    )

def record_injection_block(threat_label: str = "malicious"):
    metrics_registry.inc_counter(
        "rag_injections_blocked_total",
        labels={"threat": threat_label}
    )

def record_evidence_validation(passed: bool):
    metrics_registry.inc_counter(
        "rag_evidence_validations_total",
        labels={"result": "accepted" if passed else "rejected"}
    )

def export_prometheus_text() -> str:
    return metrics_registry.generate_metrics_text()
