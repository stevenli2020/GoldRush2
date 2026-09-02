"""Shared data-source collectors."""

from goldrush2.collectors.fed import FedCollector
from goldrush2.collectors.gpr import GPRCollector
from goldrush2.collectors.ofac import OFACCollector

__all__ = ["FedCollector", "GPRCollector", "OFACCollector"]
