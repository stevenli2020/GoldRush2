"""Shared data-source collectors."""

from goldrush2.collectors.fed import FedCollector
from goldrush2.collectors.gpr import GPRCollector
from goldrush2.collectors.ofac import OFACCollector
from goldrush2.collectors.cftc import CFTCCollector

__all__ = ["CFTCCollector", "FedCollector", "GPRCollector", "OFACCollector"]
