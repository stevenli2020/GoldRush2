"""Shared data-source collectors."""

from goldrush2.dr2.collectors.fed import FedCollector
from goldrush2.dr2.collectors.gpr import GPRCollector
from goldrush2.dr2.collectors.ofac import OFACCollector
from goldrush2.dr2.collectors.cftc import CFTCCollector
from goldrush2.dr2.collectors.cme_futures import CMEFuturesCollector
from goldrush2.dr2.collectors.fedwatch import FedWatchCollector
from goldrush2.dr2.collectors.cme import CMECurveCollector
from goldrush2.dr2.collectors.ois import OISCollector

__all__ = ["CFTCCollector", "CMEFuturesCollector", "CMECurveCollector", "FedCollector", "FedWatchCollector", "GPRCollector", "OISCollector", "OFACCollector"]
