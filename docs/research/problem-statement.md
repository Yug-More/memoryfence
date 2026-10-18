# Problem Statement

**Status:** Phase 1 proposal. No experiments have been run, and nothing in this document is an empirical finding.

## 1. Context

**Collaborative AI agents.** Workplace assistants increasingly act for individual users inside shared workspaces: team chat, documents, tickets, and meeting notes. Each user has a personal agent that can read shared material and call tools (send messages, share documents, change permissions) with that user's privileges.

**Persistent memory systems.** To be useful across sessions, these agents keep long-term memory. Memory pipelines rarely store raw content verbatim. They extract facts, summarize threads, merge overlapping entries, and synthesize higher-level "reflections" ([Park2023], [Packer2023], [Chhikara2025]).

**Shared organizational knowledge.** In a team setting, the same ingested material feeds many users' agents. A memory built from a shared channel may be retrieved by the agent of anyone who can see that channel, even though the memory's content was written by someone else.

## 2. Concepts

| Term | Meaning in this project |
|---|---|
| **Principal** | An authenticated human user of the workspace, with a role and permissions. |
| **Cross-user trust boundary** | The boundary between principals. Content one principal authors is not authoritative for another principal's agent, even when both can read it. Workspace access control decides who may *read* content; it does not decide whose *instructions* an agent should follow. |
| **Lower-trust source material** | Shared content authored by a principal other than the agent's user and without instruction authority over that user, for example a peer's message, a guest's comment, or an external collaborator's document. |
| **Memory transformation** | An LLM-mediated operation that turns sources or existing memories into new memory records: summarization, merging (consolidation), reflection, and repeated rounds of these. |
| **Derived memory** | A memory record produced by a transformation. Its content depends on one or more inputs, which may come from several principals. |
| **Source deletion** | Removal of a source by its author, a moderator, or a retention policy. |
| **Provenance** | The record of where a memory came from: which sources and memories were inputs to each transformation, and who authored each source. MemoryFence distinguishes **true provenance**, the complete ground truth known only to the evaluation harness, from **recorded provenance**, what the system under test actually captured. |
| **Provenance loss** | Recorded provenance that is less complete than true provenance, for example a derived memory whose recorded inputs omit an attacker-authored source. |
| **Unauthorized downstream behavior** | A victim agent action that the victim did not request and would not authorize, such as sharing a private document with an outsider. |

## 3. The security problem

Consider a workspace member, the **attacker**, who can author shared content but cannot act with a colleague's privileges. If the attacker places an instruction in shared content, and a memory transformation carries that instruction into a derived memory, a different member's agent (the **victim agent**) may later retrieve it and act on it with the victim's privileges. This is a *confused-deputy* escalation mediated by memory. The attack never violates workspace access control: every read and every tool call stays within permissions that someone legitimately holds.

Two properties distinguish this setting from single-session indirect prompt injection:

1. **Provenance can be lost in transformation.** A summary or reflection may restate attacker text in neutral or authoritative language, attribute it to "the team", or merge it with legitimate content. Defenses that rely on knowing where content came from (role separation, spotlighting, trust labels) may no longer see the attacker as its origin ([Xu2026]).
2. **Deletion may not reach derived state.** If the attacker deletes the source to remove evidence, or a moderator deletes it as remediation, a derived memory may continue to carry the instruction with no visible link to a deleted, attacker-authored source.

## 4. Why deleting a source does not guarantee removal

Deleting a source removes one record. Whether it also removes the source's *influence* depends on what the platform does with everything derived from it:

- **Derived memories are separate records.** A summary written yesterday is its own row in the memory store. Deleting the source document does not delete or rewrite that row unless the platform explicitly propagates the deletion.
- **Propagation needs provenance.** To find what to remove, the platform must know which memories were derived from the source, directly or through several rounds. It can only follow the links it recorded. A memory whose derivation was never linked to the source is invisible to any deletion cascade.
- **Derived content mixes inputs.** A consolidated memory may combine the attacker's note with legitimate material. Deleting it removes useful content as well; keeping it keeps the instruction; regenerating it from the remaining inputs costs computation and depends on knowing which inputs remain.
- **Influence can be re-seeded.** Before the deletion, an agent may already have written new content (a weekly update, a new note) that restates the instruction. That content has its own lifecycle.

Each of these points corresponds to a deletion policy that MemoryFence compares (see [`experimental-protocol.md`](experimental-protocol.md#32-deletion-policies)). Prior work has shown, mainly in privacy settings, that source-level deletion leaves derived influence intact ([Yao2026], [Ren2026], [Xie2026Bemula], [Yu2026]). MemoryFence treats that as an expected replication, not a discovery.

## 5. Persistence is not compromise

An instruction that survives in memory has not necessarily caused harm. MemoryFence keeps these outcomes separate:

| Outcome | Question | Why it is distinct |
|---|---|---|
| **Survived** | Does any derived memory still contain the instruction? | The memory may never be retrieved. |
| **Retrieved** | Did a memory with attacker-origin content reach the victim agent's context? | The model may ignore it. |
| **Followed** | Did the agent's reasoning adopt the instruction? | The agent may never act on it. |
| **Proposed** | Did the agent emit a tool call that serves the attacker's objective? | Authorization may block it. |
| **Executed** | Did that call pass authorization and change sandbox state? | Only this is an unauthorized action. |

Reporting only end-to-end success hides where a defense works. Reporting only survival or retrieval overstates the threat. [Leong2026] reports that storage of malicious instructions can be near-universal while execution varies widely, which is exactly why the stages must be measured separately.

## 6. Prior work and the gap

Prior work has demonstrated each element separately. It shows that:

- cross-user poisoning of shared agent state leads to actions on behalf of benign users ([Patlan2025], [Dong2025]);
- consolidation launders provenance ([Xu2026]);
- summaries conceal revoked or poisoned ancestry, and provenance-aware gating mitigates this ([Wang2026MAP], [Ouyang2026]);
- source deletion leaves derived artifacts active in privacy settings ([Yao2026]);
- remediation strategies differ in recovery and cost when faulty memories are already diagnosed ([Yu2026]).

See [`literature-review.md`](literature-review.md) for a complete account.

What remains under-measured is **how these factors interact under controlled variation**:

- how transformation type and repeated transformation affect whether an instruction payload survives;
- how different deletion policies change residual unauthorized behavior when deletion is an ordinary event rather than a diagnosed incident;
- how much deletion policies and provenance-aware defenses degrade when recorded provenance *silently* omits derivation links, compared with authorization that does not depend on provenance;
- what these defenses cost in legitimate task completion, especially when a legitimate colleague's instruction *should* be followed.

## 7. Research question

> **Under what conditions can attacker-origin instructions persist in derived AI memories after transformations or original-source deletion, and how do deletion handling, provenance completeness, and defense mechanisms influence unauthorized downstream agent behavior?**

This is a research question, not a claim. It is decomposed into six testable sub-questions:

| ID | Topic | Sub-question |
|---|---|---|
| **RQ1** | Transformation depth | How do the type and depth of memory transformation affect whether an attacker's instruction payload survives into derived memories in a form that can still direct behavior? |
| **RQ2** | Deletion handling | After the attacker's source is deleted, how often does a victim agent still retrieve, follow, propose, and execute the instruction under each deletion policy? |
| **RQ3** | Defense effectiveness | How do prompt-level delimiting, provenance-aware retrieval, independent action authorization, and lineage-gated authorization compare in attack success at each outcome stage? |
| **RQ4** | Provenance completeness | How sensitive are deletion policies and each defense to incomplete recorded provenance? |
| **RQ5** | Unauthorized tool execution | Where along the funnel (retrieved, followed, proposed, executed) does compromise stop under each condition, and how often does an unauthorized proposal become an executed action? |
| **RQ6** | Legitimate task preservation | What does each deletion policy and defense cost in benign task success, legitimate-instruction compliance, false positives, and overhead? |

Testable predictions are in [`hypotheses.md`](hypotheses.md), and the experimental design is in [`experimental-protocol.md`](experimental-protocol.md).

## 8. Proposed contribution

MemoryFence proposes a **narrow, defensible contribution**:

1. An **open, reproducible evaluation harness** for collaborative-agent memory, with explicit models of principals, shared sources, memory transformations, true and recorded provenance, deletion policies, and sandboxed tool execution.
2. A **preregistered measurement study** that varies transformation, deletion handling, defense configuration, and recorded-provenance completeness, and reports a four-stage outcome funnel with uncertainty estimates.
3. **Independent replications** of conditions that resemble published settings, so results can be compared with prior reports and discrepancies explained.

MemoryFence does **not** claim to introduce a new attack class or a new defense mechanism. Defenses are implemented as *mechanisms inspired by* published designs and are labeled as such.

## 9. Why it matters

- **Remediation assumptions.** Organizations often treat deleting malicious content as remediation. If derived memories survive deletion, incident response that stops at the source is incomplete.
- **Audit and attribution.** When the source is gone, an unauthorized action may appear to originate from the victim's own memory, which complicates attribution (compare [arXiv:2605.22842](https://arxiv.org/abs/2605.22842), listed as not yet reviewed).
- **Design guidance.** Teams choosing between provenance tracking, deletion cascades, and action-time authorization need comparative evidence on effectiveness and cost, not only isolated demonstrations.

## 10. Out of scope

The problem is bounded by the threat model in [`threat-model.md`](threat-model.md). In particular, MemoryFence does not address model-weight poisoning, infrastructure compromise, self-propagating worms, multimodal payloads, or privacy leakage of deleted information except where leakage occurs through an unauthorized action.
