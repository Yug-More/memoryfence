# Expanded v1 benchmark

Frozen at implementation commit `4a430fa` on 7 November 2026, after protocol commit
`9d56faa`. `scenarios.json` contains **80 case configurations /16 graph-operation
families**, not 80 unrelated natural-language attacks. Each family has complete,
marked-partial and silent-partial attack cases, a clean-source deletion control,
and a never-exposed control. Stable IDs identify family and condition.

Families f01–f12 are development (60 cases); f13–f16 evaluation (20 cases). Five
counterfactuals stay grouped. Shape/operation signatures differ across families;
the validator prevents exact signature duplication and split leakage, not all
possible semantic similarity. All families share a fixed synthetic objective.

The 16 manually specified DAGs include single copies, chains of depths 2 and 4,
fan-out, joins, a diamond, mixed-source and late three-source aggregation, and
repeated update-shaped chains. Each family uses one seed (1101–1116). Primary source
records have one uniquely identified fact each. Target origin labels and fixture
ancestry are evaluator annotations, never defense inputs. Source kinds cycle over
document/email/repository-file/knowledge-base/tool-response fixture representations.

TT1–TT4 use production transformation services but the expanded backend unions
supplied facts for every operation. These fixtures do not simulate semantic
paraphrasing or model reasoning. Fact lookup asks for `clean-fact`; every strategy
excludes primary memory from answer context and uses top five allowed derived hits.

The expected invariants are: never-exposed graphs contain no target-origin fact;
complete cascade invalidates true target descendants; complete DS4 projects only
surviving facts; marked gaps permit containment; silent gaps need not be detectable;
clean deletion must not be confused with attack success. Exact outcomes depend on
recorded edges and are evaluated from raw state, not hard-coded expected scores.

Regenerate to a **new** path, then compare without changing the frozen file:

```bash
python scripts/research/generate_expanded.py --output /tmp/expanded-v1-regenerated.json
cmp benchmarks/expanded-v1/scenarios.json /tmp/expanded-v1-regenerated.json
uv run --frozen memoryfence expanded validate --dataset benchmarks/expanded-v1/scenarios.json
```

The generator is a transparent enumeration of hand-specified templates, not a
stochastic scenario-discovery method. 80 deliberately falls below the 150–300
planning target; adding lexical copies would not increase independent evidence.
See `docs/EXPERIMENTAL_METHODOLOGY.md` for predeclared metrics, exclusions and paired
analysis, and `docs/RESULTS.md` for measured outcomes and accession members.
