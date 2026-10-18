"""Map hypotheses to metrics. This does not revise or confirm them."""

from typing import Literal

from memoryfence.domain.base import DomainModel

Status = Literal["procedure_available", "not_computable"]


class HypothesisLink(DomainModel):
    hypothesis_id: str
    research_question: str
    comparison: str
    metric: str
    planned_test: str
    status: Status
    note: str


def hypothesis_links() -> tuple[HypothesisLink, ...]:
    """The confirmatory family as written. Scripted fixtures do not test it."""
    return (
        HypothesisLink(
            hypothesis_id="H1",
            research_question="RQ1",
            comparison="transformation depth 1 vs 2 vs 3",
            metric="S0 payload survival",
            planned_test="one-sided Cochran-Armitage trend",
            status="not_computable",
            note="Depth is not a runner factor, and the trend test is not implemented.",
        ),
        HypothesisLink(
            hypothesis_id="H2a",
            research_question="RQ2",
            comparison="DS1 vs DS0",
            metric="paired risk difference of S4",
            planned_test="paired non-inferiority, margin 0.05",
            status="not_computable",
            note="The paired interval exists. TOST-style non-inferiority is not implemented.",
        ),
        HypothesisLink(
            hypothesis_id="H2b",
            research_question="RQ2",
            comparison="DS2 vs DS1 at LF1.0",
            metric="S4",
            planned_test="exact McNemar",
            status="procedure_available",
            note="The statistic can be computed. A scripted fixture is not confirmation.",
        ),
        HypothesisLink(
            hypothesis_id="H3a",
            research_question="RQ3",
            comparison="DF2 vs DF0",
            metric="S4",
            planned_test="exact McNemar",
            status="procedure_available",
            note="The statistic can be computed. A scripted fixture is not confirmation.",
        ),
        HypothesisLink(
            hypothesis_id="H3b",
            research_question="RQ3",
            comparison="DF3 vs DF0",
            metric="S4",
            planned_test="exact McNemar",
            status="procedure_available",
            note="The statistic can be computed. A scripted fixture is not confirmation.",
        ),
        HypothesisLink(
            hypothesis_id="H3c",
            research_question="RQ6",
            comparison="DF2-exclude vs DF0 on C-LEGIT",
            metric="legitimate-instruction compliance",
            planned_test="exact McNemar",
            status="procedure_available",
            note="The statistic can be computed. A scripted fixture is not confirmation.",
        ),
        HypothesisLink(
            hypothesis_id="H4",
            research_question="RQ4",
            comparison="defense by lineage fidelity",
            metric="S4",
            planned_test="mixed-effects interaction and TOST",
            status="not_computable",
            note="Mixed-effects logistic regression and TOST are not implemented.",
        ),
    )
