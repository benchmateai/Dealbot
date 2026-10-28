"""The funnel: cheapest check first. Free cut on data in hand, one-call checks, hard facts in code,
Jev, then one final pick. Every rejection is logged with the check that fired and benched."""

from filter.funnel import Candidate, Funnel, FunnelContext, FunnelResult, Rejection, Stage, StageCount
from filter.stages import FinalPick, FreeCut, HardFacts, JevStage, OneCall

__all__ = ["Candidate", "FinalPick", "FreeCut", "Funnel", "FunnelContext", "FunnelResult", "HardFacts", "JevStage", "OneCall", "Rejection", "Stage", "StageCount"]
