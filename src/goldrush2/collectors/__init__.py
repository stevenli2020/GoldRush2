"""Shared data-source collectors."""

from goldrush2.collectors.fed import FedCollector
from goldrush2.collectors.gpr import GPRCollector
from goldrush2.collectors.ofac import OFACCollector
from goldrush2.collectors.cftc import CFTCCollector
from goldrush2.collectors.cme_futures import CMEFuturesCollector
from goldrush2.collectors.fedwatch import FedWatchCollector

__all__ = ["CFTCCollector", "CMEFuturesCollector", "FedCollector", "FedWatchCollector", "GPRCollector", "OFACCollector"]
