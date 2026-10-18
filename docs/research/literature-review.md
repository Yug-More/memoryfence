# Literature Review

**Status:** Phase 1 working review. Bibliographic metadata re-verified on 18 October 2026.
**Scope:** prompt injection against LLM agents; persistent memory poisoning; cross-user and multi-agent propagation; memory consolidation and provenance; source deletion and derived-state persistence; access control and runtime authorization of agent actions; benchmarks and defenses.

This review places MemoryFence's research question within existing work and identifies what remains unaddressed. Its most important conclusion comes first.

## Key finding: substantial overlap with recent work

The central research question asks under what conditions attacker-origin instructions persist in derived memories after transformation or source deletion, and how deletion handling, provenance completeness, and defenses influence unauthorized downstream behavior. **It is not novel as a whole.** Between late 2025 and October 2026, several preprints addressed most of its components:

| Component of the MemoryFence question | Closest prior work (entries below) |
|---|---|
| A different user poisons shared persistent state, and the agent later acts for a benign user | MURMUR [Patlan2025], MINJA [Dong2025], SMSR [Sharma2026] |
| Shared memory with provenance and access control across users | Collaborative Memory [Rezazadeh2025], GateMem [Ren2026], MAP-Graph [Wang2026MAP] |
| LLM memory consolidation preserves an action trigger while erasing its low-trust source | Memory Provenance Laundering / PPMF [Xu2026] |
| Summaries conceal poisoned or revoked sources; provenance-aware retrieval with risk-gated actions | MAP-Graph [Wang2026MAP], MemLineage [Ouyang2026] |
| Deleting a source record leaves derived artifacts active | Execution-state unlearning [Yao2026], dependency-guided rollback [Yu2026], GateMem [Ren2026], Bemula [Xie2026Bemula] |
| Comparing remediation strategies (reset, delete retrieved, rollback) for faulty memory | Dependency-guided rollback [Yu2026] |
| Provenance-dependent defenses under missing or degraded provenance | PPMF metadata masking [Xu2026], MemLineage attribution-decay sweep [Ouyang2026] |
| Storing a malicious instruction is separable from executing it | Injection-Execution Dissociation [Leong2026], sleeper memory poisoning [Pulipaka2026] |
| Deterministic, policy-based authorization of tool calls | CaMeL [Debenedetti2025], Progent [Shi2025], FIDES [Costa2025], f-secure [Wu2024IFC], PFI [Kim2025] |

Consequently, MemoryFence **must not claim** to be the first to show that poisoned memories survive summarization, that deletion fails to remove derived memories, that provenance-aware gating blocks unauthorized actions, or that provenance-dependent defenses depend on provenance quality.

### What appears less covered

The following combination does not appear in any single work we reviewed (review depth varies; see section 1.3):

1. **Deletion handling as a controlled factor against cross-principal instruction payloads, measured by downstream unauthorized actions.** Prior deletion work mostly measures *privacy leakage* of deleted facts ([Yao2026], [Ren2026], [Xie2026Bemula], [Lin2026]). [Yu2026] compares remediation strategies, but for *post-failure recovery* given an already diagnosed set of faulty memories, scored by answer recovery rather than by whether an attacker's instruction still drives actions. MAP-Graph [Wang2026MAP] evaluates revocation as a benchmark-supplied field with a single remediation behavior (mark descendants), one templated round, and single temperature-zero runs.
2. **Transformation type and depth as a dose variable** for LLM-mediated rewriting (extractive summary, abstractive summary, multi-source consolidation, reflection, over repeated rounds), with payload survival measured separately from downstream behavior. MemLineage [Ouyang2026] sweeps chain length, but at the level of its label-propagation rule under synthetic attribution-weight schedules, not by measuring whether real transformations carry a payload.
3. **Silent loss of recorded lineage edges.** PPMF [Xu2026] masks provenance *fields*; missing fields are visible and fail closed (no unauthorized execution observed, with lower benign success). Whether a derivation edge was never recorded is different: the derived memory simply appears to have fewer, possibly only trusted, ancestors. We did not find a study that measures how deletion policies and retrieval-time defenses degrade under silent edge loss, compared with authorization that does not read lineage.
4. **A staged outcome funnel** (retrieved, followed, proposed, executed) applied uniformly across these conditions. [Leong2026] and [Pulipaka2026] separate storage, retrieval, and use, but not across deletion and lineage conditions.
5. **The cost of provenance-based blocking on legitimate cross-principal instructions,** for example a team lead's workflow note that a colleague's agent *should* follow.

### Recommended defensible contribution

MemoryFence should be positioned as **an independent, preregistered, reproducible measurement study and open harness**, not as a new attack or defense:

> A controlled evaluation of how **memory transformation type and depth**, **deletion handling**, and **recorded-provenance completeness** affect the persistence of cross-principal instruction payloads in a collaborative agent workspace. Outcomes are measured at four separate stages (retrieval, instruction following, action proposal, sandboxed execution). The study compares provenance-aware retrieval with independent action authorization, including utility and false-positive costs on legitimate cross-principal instructions.

Defense implementations in MemoryFence should be described as *mechanisms inspired by* published designs (for example "PPMF-style authority matching" or "MemLineage-style lineage gating"), never as faithful reproductions unless validated against the original artifacts.

This recommendation is reflected in [`problem-statement.md`](problem-statement.md) and [`hypotheses.md`](hypotheses.md).

---

## 1. Review method

### 1.1 Search strategy

- **arXiv API** queries on title and abstract terms, including `"memory poisoning" AND agent`, `"memory injection" AND agent`, `"cross-user" AND LLM`, `"shared memory" AND "prompt injection"`, `provenance AND memory AND agent AND poisoning`, `"memory consolidation" AND attack`, `agent AND memory AND unlearning`, `"derived memories"`, and `"multi-tenant" AND agent AND memory`. A refresh on 18 October 2026, sorted by submission date, surfaced three additional titles (section 11).
- **Backward snowballing** from the related-work sections of the closest papers (MAP-Graph, MURMUR, MemLineage, PPMF).
- **The owner's earlier manuscript draft,** which cited four sources not previously in this review (MemoryGraft, sleeper memory poisoning, Collaborative Memory, NetInjectBench). All four were verified and added.
- **Authoritative non-academic sources:** OWASP GenAI Security Project, NIST, MITRE ATLAS, W3C, vendor security advisories, and published security research disclosures.

### 1.2 Verification

On 18 October 2026, every arXiv identifier in this document (79 in total) was resolved through the arXiv API, and the returned title, author list, and first-submission date were compared with the entry. All identifiers resolved, and no metadata mismatch was found. In particular, the nine candidate identifiers named in the project brief (MURMUR 2511.17671, MINJA 2503.03704, PPMF 2607.29167, MAP-Graph 2608.10509, MemLineage 2605.14421, execution-state unlearning 2609.04875, GateMem 2606.18829, rollback repair 2608.10502, Injection-Execution Dissociation 2605.08442) all correspond to the papers described below.

Venue claims rely on the arXiv `journal_ref` field or author comments, or on DOIs. Where a published title differs from the arXiv title, both are given. Venues stated only in author comments are labeled "per arXiv comment" and are not independently confirmed. Also on 18 October 2026, every non-arXiv URL in this document returned HTTP 200, and every DOI resolved to its publisher with Crossref title, venue, and year matching the entry. ACM Digital Library pages refuse automated requests, so the three ACM DOIs were confirmed through Crossref only.

### 1.3 Review depth

Each entry carries one of these labels, and its claims are limited accordingly.

- **[F] Full text.** The complete paper, including appendices, was read.
- **[P] Partial full text.** The threat model, method, results, and limitations sections were read in addition to the abstract.
- **[A] Abstract and metadata.** Only the abstract was reviewed. "Threat model" and "limitations" fields record only what the abstract supports, or are marked *not determinable from abstract*.

Numerical results quoted below are **the authors' reported results**, reproduced only where they appear in the reviewed text. MemoryFence has not reproduced any of them.

### 1.4 Caveats

- **Most 2026 entries are preprints** without verified peer review. Their findings should be treated as provisional.
- The literature is growing rapidly. Section 11 lists papers identified but not yet reviewed. The review must be refreshed before the study is preregistered.
- The Microsoft agentic failure-modes whitepaper and the MSRC advisory page could not be retrieved programmatically and are cited only through alternative verified records, as noted.

---

## 2. Prompt injection foundations

### [Perez2022] Ignore Previous Prompt: Attack Techniques For Language Models
- **Authors:** Fábio Perez, Ian Ribeiro
- **Year / venue:** 2022, NeurIPS ML Safety Workshop (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2211.09527>
- **Review depth:** A
- **Research question:** How easily can adversarial user prompts override an application's instructions?
- **Threat model:** A user directly supplies adversarial input to an LLM-backed application (direct injection).
- **Methodology:** A framework of handcrafted attack prompts for goal hijacking and prompt leaking.
- **Main findings:** Simple handcrafted inputs can misalign model behavior from the application's intent.
- **Limitations:** Direct injection only; no tools, memory, or third-party data.
- **Relationship to MemoryFence:** Historical baseline. MemoryFence concerns *indirect*, persisted, cross-principal injection.

### [Greshake2023] Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection
- **Authors:** Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, Mario Fritz
- **Year / venue:** 2023, Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security (AISec '23)
- **Link:** DOI [10.1145/3605764.3623985](https://doi.org/10.1145/3605764.3623985); <https://arxiv.org/abs/2302.12173>
- **Review depth:** A
- **Research question:** Can adversaries with no direct interface to an LLM application control it by planting prompts in data the application retrieves?
- **Threat model:** A remote attacker places instructions in content likely to be retrieved (web pages, documents, email).
- **Methodology:** A security-oriented taxonomy and demonstrations against real-world and synthetic LLM-integrated applications.
- **Main findings:** LLM-integrated applications blur the line between data and instructions. Impacts include data theft, worming, and information-ecosystem contamination.
- **Limitations:** Demonstrations rather than controlled measurement. Persistence across memory transformations is not studied.
- **Relationship to MemoryFence:** Defines the indirect-injection threat class MemoryFence builds on. The shared source in MemoryFence is an instance of retrieved untrusted data.

### [Liu2024] Formalizing and Benchmarking Prompt Injection Attacks and Defenses
- **Authors:** Yupei Liu, Yuqi Jia, Runpeng Geng, Jinyuan Jia, Neil Zhenqiang Gong
- **Year / venue:** 2024, USENIX Security Symposium (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2310.12815>
- **Review depth:** A
- **Research question:** Can prompt injection attacks and defenses be formalized and compared systematically?
- **Threat model:** An attacker controls part of the data an LLM-integrated application processes.
- **Methodology:** A formal framework subsuming existing attacks, a combined attack, and an evaluation of 5 attacks and 10 defenses across 10 LLMs and 7 tasks.
- **Main findings:** Provides a common benchmark platform (Open-Prompt-Injection).
- **Limitations:** Single-turn tasks without persistent memory or tool execution.
- **Relationship to MemoryFence:** Methodological precedent for systematic multi-model comparison and a formal definition of attack success.

## 3. Agent prompt-injection benchmarks

### [Zhan2024] InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents
- **Authors:** Qiusi Zhan, Zhixiang Liang, Zifan Ying, Daniel Kang
- **Year / venue:** 2024, Findings of ACL 2024
- **Link:** DOI [10.18653/v1/2024.findings-acl.624](https://doi.org/10.18653/v1/2024.findings-acl.624); <https://arxiv.org/abs/2403.02691>
- **Review depth:** A
- **Research question:** How vulnerable are tool-integrated agents to indirect prompt injection?
- **Threat model:** Malicious instructions are embedded in external content returned by user tools. Attacker goals are direct harm or data exfiltration.
- **Methodology:** 1,054 test cases spanning 17 user tools and 62 attacker tools; 30 agents evaluated.
- **Main findings:** Agents are vulnerable. The authors report that ReAct-prompted GPT-4 was vulnerable in 24% of cases in the base setting.
- **Limitations:** Single session; no persistent memory.
- **Relationship to MemoryFence:** Its taxonomy of attacker intentions (harm vs. exfiltration) is adapted to MemoryFence's sandbox action objectives.

### [Debenedetti2024] AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents
- **Authors:** Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, Florian Tramèr
- **Year / venue:** 2024. The arXiv record lists no venue. It is commonly cited as NeurIPS 2024 Datasets and Benchmarks Track; **not verified for this review**.
- **Link:** <https://arxiv.org/abs/2406.13352>
- **Review depth:** A
- **Research question:** How can prompt injection attacks and defenses for tool-using agents be evaluated in an extensible, dynamic way?
- **Threat model:** Data returned by external tools hijacks the agent to perform attacker tasks.
- **Methodology:** An extensible environment with 97 tasks and 629 security test cases (email, banking, travel), with pluggable attacks and defenses.
- **Main findings:** Both attacks and defenses are challenged. State-of-the-art models fail many tasks even without attack.
- **Limitations:** Single user and largely stateless across sessions.
- **Relationship to MemoryFence:** The primary design reference for jointly measuring utility and security in sandboxed tool environments. MURMUR [Patlan2025], PPMF [Xu2026], and MemLineage [Ouyang2026] all build on AgentDojo environments. MemoryFence should consider an AgentDojo adapter for comparability (see ADR-0001).

### [Zhang2025ASB] Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents
- **Authors:** Hanrong Zhang, Jingyuan Huang, Kai Mei, Yifei Yao, Zhenting Wang, Chenlu Zhan, Hongwei Wang, Yongfeng Zhang
- **Year / venue:** 2025, ICLR 2025 (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2410.02644>
- **Review depth:** A
- **Research question:** Can attacks and defenses across all stages of agent operation be benchmarked in one framework?
- **Threat model:** Several, including prompt injection, memory poisoning, and a Plan-of-Thought backdoor.
- **Methodology:** 10 scenarios, more than 400 tools, 27 attack and defense types, 13 LLM backbones.
- **Main findings:** Vulnerabilities exist at every stage, including memory retrieval.
- **Limitations:** Memory poisoning is one attack among many; transformation and deletion are not studied.
- **Relationship to MemoryFence:** Shows that memory retrieval is a recognized attack stage. MemoryFence's stage decomposition is finer-grained for memory specifically.

### [Jiang2026] AgentLAB: Benchmarking LLM Agents against Long-Horizon Attacks
- **Authors:** Tanqiu Jiang, Yuhui Wang, Jiacheng Liang, Ting Wang
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2602.16901>
- **Review depth:** A
- **Research question:** How susceptible are agents to adaptive, multi-turn, long-horizon attacks?
- **Threat model:** Attacks exploiting multi-turn user-agent-environment interaction, including memory poisoning.
- **Methodology:** 28 environments, 644 security test cases, 5 attack types.
- **Main findings:** Agents remain highly susceptible, and single-turn defenses do not reliably transfer.
- **Limitations:** Not determinable from abstract.
- **Relationship to MemoryFence:** Supports the premise that single-turn defenses are insufficient against persistent threats.

### [Ruan2024] Identifying the Risks of LM Agents with an LM-Emulated Sandbox (ToolEmu)
- **Authors:** Yangjun Ruan, Honghua Dong, Andrew Wang, Silviu Pitis, Yongchao Zhou, Jimmy Ba, Yann Dubois, Chris J. Maddison, Tatsunori Hashimoto
- **Year / venue:** 2023 preprint. Commonly cited as ICLR 2024; **not verified for this review**.
- **Link:** <https://arxiv.org/abs/2309.15817>
- **Review depth:** A
- **Research question:** Can tool execution be emulated by an LM to identify agent risks at scale?
- **Methodology:** LM-emulated tools and an LM-based safety evaluator.
- **Relationship to MemoryFence:** MemoryFence deliberately uses **deterministic, code-defined** simulated tools instead of LM emulation, so that "executed" is an objective outcome (see [`experimental-protocol.md`](experimental-protocol.md)).

### [Shayoni2026] NetInjectBench: Benchmarking Indirect Prompt Injection in Tool-Using Large Language Model Agents for Network Operations
- **Authors:** Ruksat Khan Shayoni, Muhammad Faraz Shoaib, S M Asif Hossain, M. F. Mridha
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2607.10490>
- **Review depth:** A
- **Research question:** How well do prompt-level, judge-based, allowlist, and metadata-aware defenses prevent unsafe tool actions from injected network-operations artifacts?
- **Methodology:** 130 scenarios separating untrusted artifact text, trusted policy metadata, and evaluation labels; three open models.
- **Main findings:** The authors report an 82.50% unsafe-action rate under naive execution; prompt-level defenses reduced it to 10–26%; static allowlisting reached 5.00% but blocked every approved change; a metadata-aware policy gate produced 0/240 unsafe actions (95% Wilson upper bound 1.58%) under a metadata-integrity assumption.
- **Limitations:** Single session; no persistent memory (per abstract).
- **Relationship to MemoryFence:** An example of reporting zero-event cells with an upper confidence bound, which MemoryFence adopts. It also illustrates the utility cost of strict allowlisting.

## 4. Persistent memory and retrieval poisoning

### [Zou2025] PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models
- **Authors:** Wei Zou, Runpeng Geng, Binghui Wang, Jinyuan Jia
- **Year / venue:** 2025, USENIX Security Symposium (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2402.07867>
- **Review depth:** A
- **Research question:** Can injecting a few texts into a RAG knowledge base force attacker-chosen answers?
- **Threat model:** The attacker can insert texts into the knowledge database.
- **Methodology:** Knowledge corruption formulated as an optimization problem.
- **Main findings:** A small number of injected texts can induce target answers.
- **Limitations:** Answer manipulation rather than agent actions; static corpus.
- **Relationship to MemoryFence:** Retrieval-stage precedent. MemoryFence's "retrieved" stage corresponds to PoisonedRAG's retrieval condition.

### [Chen2024AgentPoison] AgentPoison: Red-teaming LLM Agents via Poisoning Memory or Knowledge Bases
- **Authors:** Zhaorun Chen, Zhen Xiang, Chaowei Xiao, Dawn Song, Bo Li
- **Year / venue:** 2024. arXiv preprint, commonly cited as NeurIPS 2024; **not verified for this review**.
- **Link:** <https://arxiv.org/abs/2407.12784>
- **Review depth:** A
- **Research question:** Can an agent's long-term memory or RAG knowledge base be backdoored so that a trigger in a user instruction retrieves malicious demonstrations?
- **Threat model:** The attacker can insert poisoned records into the memory or knowledge base and place a trigger in user queries.
- **Methodology:** Optimizes backdoor triggers through constrained optimization in embedding space.
- **Main findings:** High attack success with limited impact on benign performance (per abstract).
- **Limitations:** Assumes write access to memory; no transformation or deletion.
- **Relationship to MemoryFence:** Establishes memory as an attack surface. MemoryFence assumes a weaker attacker who writes only to shared sources, never to memory directly.

### [Dong2025] Memory Injection Attacks on LLM Agents via Query-Only Interaction (MINJA)
- **Authors:** Shen Dong, Shaochen Xu, Pengfei He, Yige Li, Jiliang Tang, Tianming Liu, Hui Liu, Zhen Xiang
- **Year / venue:** 2025, arXiv preprint (venue not verified)
- **Link:** <https://arxiv.org/abs/2503.03704>
- **Review depth:** A
- **Research question:** Can an attacker inject malicious memory records only by interacting with the agent through queries?
- **Threat model:** An attacker without direct memory access shares the agent's memory bank with a **victim user**. Malicious records later steer the victim's queries.
- **Methodology:** Bridging steps link victim queries to malicious reasoning; indication prompts are progressively shortened.
- **Main findings:** Query-only interaction suffices to plant effective malicious records (per abstract).
- **Limitations:** Memory records are stored as-is; summarization and deletion are not studied.
- **Relationship to MemoryFence:** **Direct overlap on the cross-user memory threat.** MemoryFence differs by placing a transformation stage and deletion events between injection and use.

### [Srivastava2025] MemoryGraft: Persistent Compromise of LLM Agents via Poisoned Experience Retrieval
- **Authors:** Saksham Sahai Srivastava, Haoyu He
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2512.16962>
- **Review depth:** A
- **Research question:** Can an attacker implant malicious "successful experiences" into an agent's long-term memory so that later, semantically similar tasks imitate them?
- **Threat model:** The attacker supplies benign-looking ingestion-level artifacts that the agent reads during execution.
- **Methodology:** Evaluated on MetaGPT's DataInterpreter agent with GPT-4o and union lexical-plus-embedding retrieval.
- **Main findings:** A small number of poisoned records can account for a large fraction of retrieved experiences on benign workloads, producing persistent behavioral drift (per abstract).
- **Limitations:** Single-user setting; no transformation or deletion factor.
- **Relationship to MemoryFence:** Supports "procedure templates" as a payload style that may survive abstraction better than explicit imperatives.

### [Sunil2026] Memory Poisoning Attack and Defense on Memory Based LLM-Agents
- **Authors:** Balachandra Devarangadi Sunil, Isheeta Sinha, Piyush Maheshwari, Shantanu Todmal, Shreyan Mallik, Shuchi Mishra
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2601.05504>
- **Review depth:** A
- **Research question:** How robust is MINJA under realistic conditions, and which defenses help?
- **Methodology:** EHR agents on MIMIC-III, varying initial memory state, number of indication prompts, and retrieval parameters, across three models.
- **Main findings:** Pre-existing legitimate memories substantially reduce attack effectiveness (per abstract). Proposes trust-scored moderation and trust-aware memory sanitization.
- **Relationship to MemoryFence:** Motivates **distractor memory volume** as a controlled variable.

### [Zou2026eTAMP] Poison Once, Exploit Forever: Environment-Injected Memory Poisoning Attacks on Web Agents
- **Authors:** Wei Zou, Mingwen Dong, Miguel Romero Calvo, Shuaichen Chang, Jiang Guo, Dongkyu Lee, Xing Niu, Xiaofei Ma, Yanjun Qi, Jiarong Jiang
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2604.02623>
- **Review depth:** A
- **Research question:** Can a single environmental observation poison a web agent's memory and activate later on other sites?
- **Threat model:** Contamination through observation only, without direct memory access.
- **Methodology:** (Visual)WebArena experiments.
- **Main findings:** Cross-session, cross-site compromise. The authors report that attack success increases under environmental stress ("frustration exploitation").
- **Relationship to MemoryFence:** Confirms realistic write paths from untrusted content into memory.

### [Huang2026PMPA] When Malicious Instructions Persist: Persistent Memory Poisoning Attack on Harness-Based Agents
- **Authors:** Shuhuai Huang, Jingfeng Zhang, Hong Jia
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2609.13889>
- **Review depth:** A
- **Research question:** Can instructions in external sources be induced into the persistent memory of harness-based agents and later trigger malicious actions?
- **Methodology:** Evaluation on OpenClaw and Claude Code across backbones, modalities, and triggers.
- **Main findings:** The authors report separate injection-success and cross-session attack-success rates, and find that a prompt-level defense reduces injection but offers limited protection once memory is poisoned.
- **Relationship to MemoryFence:** Supports separating "written to memory" from "acted upon".

### [Pulipaka2026] Hidden in Memory: Sleeper Memory Poisoning in LLM Agents
- **Authors:** Sidharth Pulipaka, Stanislau Hlebik, Leonidas Raghav, Sahar Abdelnabi, Vyas Raina, Ivaxi Sheth, Mario Fritz
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2605.15338>
- **Review depth:** A
- **Research question:** Can manipulated external context cause an assistant to store a fabricated memory about the user that later steers conversations and actions?
- **Threat model:** The adversary controls external context (a document, web page, or repository) but not the memory store.
- **Methodology:** Evaluates the full pipeline separately: whether poisoned memories are written, later retrieved, and then used to steer conversations, across stateful assistants.
- **Main findings:** The authors report that poisoned memories are written and, among successful retrievals, frequently cause attacker-intended agentic actions (per abstract).
- **Limitations:** Single-user personal-assistant setting; no deletion factor (per abstract).
- **Relationship to MemoryFence:** **Methodological overlap on staged outcomes** (written, retrieved, used). MemoryFence adds cross-principal provenance, transformation depth, and deletion handling.

### [Dash2026] From Untrusted Input to Trusted Memory: A Systematic Study of Memory Poisoning Attacks in LLM Agents
- **Authors:** Pritam Dash, Tongyu Ge, Aditi Jain, Tanmay Shah, Zhiwei Shang
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2606.04329>
- **Review depth:** A
- **Research question:** What write channels and structural vulnerabilities enable memory poisoning?
- **Methodology:** A taxonomy of four write channels, nine structural vulnerabilities, and six attack classes; the MPBench benchmark.
- **Main findings:** Agents that write and retrieve memory more aggressively are more exploitable, and existing prompt-injection defenses do not cover memory poisoning (per abstract).
- **Relationship to MemoryFence:** A taxonomy to align MemoryFence's write channels with. Memory-write aggressiveness should be held fixed or recorded as a covariate.

### [Xie2026MemEvo] MemEvoBench: Benchmarking Safety Risks from Memory Misevolution in LLM Agents
- **Authors:** Weiwei Xie, Shaoxiong Guo, Fan Zhang, Tian Xia, Xue Yang, Lizhuang Ma, Junchi Yan, Qibing Ren
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2604.15774>
- **Review depth:** A
- **Relationship to MemoryFence:** Studies gradual behavioral drift from accumulated misleading memory. This is adjacent to MemoryFence's transformation-depth variable but concerns misinformation rather than instruction payloads.

### [Leong2026] Injection-Execution Dissociation: A Mechanistic Evaluation of Persistent Memory Attacks and Defenses in Stateful LLM Agents
- **Authors:** Jun Wen Leong
- **Year / venue:** 2026, arXiv preprint (v5)
- **Link:** <https://arxiv.org/abs/2605.08442>
- **Review depth:** A
- **Research question:** Are prompt-injection success and tool-execution success separable properties in agents with persistent memory?
- **Threat model:** Delayed-trigger attacks that persist across sessions through RAG retrieval.
- **Methodology:** A 5,040-run factorial experiment across nine open models (N = 40 per condition) evaluating six defenses at four architectural layers.
- **Main findings:** The author reports storage rates above 97.5% while execution ranged from 0% to 95% with no correlation to storage. Defense effectiveness depended on where the defense sits relative to the authority boundary, and a tool-layer "Memory Sandbox" performed best.
- **Limitations:** Single author; preprint. The companion paper [Leong2026b] publicly withdrew earlier claims, which shows transparent revision but argues for cautious reliance.
- **Relationship to MemoryFence:** **Methodological overlap on staged outcomes.** MemoryFence extends the two-stage distinction to four stages and adds transformation and deletion factors.

### [Leong2026b] Retrieval Observability Bounds on Provenance Detection for Agent Memory Poisoning: Measured Coverage and a Falsified Standalone Detector
- **Authors:** Jun Wen Leong
- **Year / venue:** 2026, arXiv preprint (v3)
- **Link:** <https://arxiv.org/abs/2606.30566>
- **Review depth:** A
- **Main findings:** Argues that trajectory-based provenance detection depends on whether memory access produces a logged tool call ("retrieval observability"). The v3 abstract explicitly reverses an earlier recommendation.
- **Relationship to MemoryFence:** Cautions against trace-based detectors and supports MemoryFence's use of harness-level true provenance as ground truth.

### [Das2026] Self-Propagating Misalignment in LLM Agents, and Why Auditing or Disabling Memory Is Not Enough
- **Authors:** Debeshee Das, Jacqueline Tay, Bruce Tsai, David Huang, Javier Rando
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2610.04083>
- **Review depth:** A
- **Main findings:** Without any external adversary, a misaligned agent can write goals to memory that a future agent executes. Removing the memory tool shifts writes to the file system (per abstract).
- **Relationship to MemoryFence:** Outside the threat model (no external attacker), but shows that persistence channels extend beyond the designated memory store, a limitation MemoryFence must acknowledge.

## 5. Cross-user and multi-agent propagation

### [Patlan2025] MURMUR: Using cross-user chatter to break collaborative language agents in groups
- **Authors:** Atharv Singh Patlan, Peiyao Sheng, S. Ashwin Hebbar, Prateek Mittal, Pramod Viswanath
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2511.17671>
- **Review depth:** P
- **Research question:** Do multi-user agents in shared workspaces admit a new attack, cross-user poisoning (CUP)?
- **Threat model:** A subset of users is adversarial. Attackers act through the public interface under normal platform constraints, send up to a budget of ordinary messages, and **cannot edit or delete transcript history**. Success means the agent executes an attacker-specified action sequence while serving a benign user.
- **Methodology:** Validates CUP on real multi-user agents. MURMUR composes single-user tasks (adapted from tau-bench Airline and AgentDojo Slack/Workspace) into concurrent group scenarios with LLM-simulated users.
- **Main findings:** CUP succeeds at high rates, persists across multiple tasks, and remains substantial under an input-filtering defense. The authors attribute this to models conditioning on coarse roles rather than fine-grained user identities, and propose task-based clustering as a first-step defense.
- **Limitations (stated):** The clustering defense does not prevent in-cluster attacks, depends on clustering accuracy, and reduced task success in some environments.
- **Relationship to MemoryFence:** **Direct overlap on cross-user attacks against collaborative agents.** MURMUR's shared state is the conversation transcript. MemoryFence studies *derived* memory produced by transformations and explicitly models deletion, which MURMUR's attacker is not permitted to do.

### [Rezazadeh2025] Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control
- **Authors:** Alireza Rezazadeh, Zichao Li, Ange Lou, Yuying Zhao, Wei Wei, Yujia Bao
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2505.18279>
- **Review depth:** A (abstract, plus passages describing the access-revocation experiment)
- **Research question:** How can multi-user, multi-agent systems share memory under asymmetric, time-varying permissions?
- **Threat model:** Not adversarial. The concern is enforcing read and write policies, not resisting poisoning.
- **Methodology:** Private and shared memory tiers; every fragment carries immutable provenance (contributing agents, accessed resources, timestamps); read policies project fragments into filtered views, and write policies apply context-aware transformations. Experiments grant and then revoke access-graph edges over time.
- **Main findings:** The authors report provable adherence to time-varying policies and that answer quality tracks granted access as permissions change.
- **Limitations:** No adversarial evaluation and no deletion of source content (revocation removes *access*, not content).
- **Relationship to MemoryFence:** **The closest system model for provenance-carrying shared memory.** It prevents MemoryFence from treating access-controlled, provenance-tagged memory as new. MemoryFence instead asks how such memory behaves when an authorized insider deliberately poisons it and then deletes the source.

### [Yang2026UCC] No Attacker Needed: Unintentional Cross-User Contamination in Shared-State LLM Agents
- **Authors:** Tiankai Yang, Jiate Li, Yi Nian, Shen Dong, Ruiyao Xu, Ryan Rossi, Kaize Ding, Yue Zhao
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2604.01350>
- **Review depth:** A
- **Main findings:** Benign interactions alone produce cross-user contamination in shared state. Write-time sanitization helps for conversational state but leaves residual risk for executable artifacts (per abstract).
- **Relationship to MemoryFence:** Motivates a **benign-contamination control** so that adversarial effects are not confused with ordinary scope errors.

### [Mudgal2026] MemLeak: Cross-User Semantic Leakage in Multi-Tenant AI Agent Memory
- **Authors:** Priyanka Mudgal, Kai Zhao, Guilin Zhang, Andy Olsen, Ezekiel Miller, Xu Chu, Aletta Johanna Blanken
- **Year / venue:** 2026. The arXiv comment states "Neurips-PALM 2026"; not independently verified.
- **Link:** <https://arxiv.org/abs/2610.04195>
- **Review depth:** A
- **Main findings:** Shared vector stores leak memories across users through ordinary similarity retrieval. The authors report that only hard post-retrieval ownership gating consistently restored the clean baseline among the mitigations they tested.
- **Relationship to MemoryFence:** Ownership gating is a simple provenance-aware retrieval baseline. Its cost for legitimate shared memories needs measuring.

### [Ren2026] GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memory Agents
- **Authors:** Zhe Ren, Yibo Yang, Yimeng Chen, Zijun Zhao, Benshuo Fu, Zhihao Shu, Bingjie Zhang, Yangyang Xu, Dandan Guo, Shuicheng Yan
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2606.18829>
- **Review depth:** P
- **Research question:** Can shared-memory agents simultaneously deliver utility, enforce access control, and honor deletion requests across multiple principals?
- **Threat model:** Governance failures rather than injected instructions: soft-overreach access requests and probing for deleted sensitive values through direct, confirmatory, reconstructive, or social-engineering queries.
- **Methodology:** Multi-party episodes across medical, office, education, and household domains, with hidden checkpoints and structured judging.
- **Main findings:** No method achieves strong utility, access control, and forgetting together. Retrieval-based and external-memory methods still leak unauthorized or deleted information.
- **Relationship to MemoryFence:** **Overlap on multi-principal shared memory and deletion.** GateMem measures disclosure of deleted *information*. MemoryFence measures persistence of deleted-source *instructions that drive actions*.

### [Lee2024] Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems
- **Authors:** Donghyun Lee, Mo Tiwari
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2410.07283>
- **Review depth:** A
- **Main findings:** Malicious prompts can self-replicate across interconnected agents. Proposes "LLM Tagging" as a defense in combination with other safeguards.
- **Relationship to MemoryFence:** LLM Tagging is a form of provenance labeling. MemoryFence asks whether such labels survive transformation.

### [Cohen2024] Here Comes The AI Worm: Unleashing Zero-click Worms that Target GenAI-Powered Applications (Morris-II)
- **Authors:** Stav Cohen, Ron Bitton, Ben Nassi
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2403.02817>
- **Review depth:** A
- **Relationship to MemoryFence:** Demonstrates self-replicating prompts propagating through RAG-based applications. Open-ended self-replication is out of scope, but re-seeding after deletion is a related propagation path that MemoryFence measures.

### [Gu2024] Agent Smith: A Single Image Can Jailbreak One Million Multimodal LLM Agents Exponentially Fast
- **Authors:** Xiangming Gu, Xiaosen Zheng, Tianyu Pang, Chao Du, Qian Liu, Ye Wang, Jing Jiang, Min Lin
- **Year / venue:** 2024, ICML 2024 (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2402.08567>
- **Review depth:** A
- **Relationship to MemoryFence:** Background on infectious propagation among agents. Multimodal attacks are out of scope.

### [Ju2024] Flooding Spread of Manipulated Knowledge in LLM-Based Multi-Agent Communities
- **Authors:** Tianjie Ju, Yiting Wang, Xinbei Ma, Pengzhou Cheng, Haodong Zhao, Yulong Wang, Lifeng Liu, Jian Xie, Zhuosheng Zhang, Gongshen Liu
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2407.07791>
- **Review depth:** A
- **Relationship to MemoryFence:** Background on manipulated knowledge spreading among agents, including persistence into RAG stores.

## 6. Memory consolidation, provenance, and lineage

### [Xu2026] Memory Provenance Laundering in LLM Agents: A Non-Amplification Firewall for Persistent Memory (PPMF)
- **Authors:** Jinghan Xu, Yiyong Xiao, Wanru Shao, Hankai Liu, Xinjin Li
- **Year / venue:** 2026, arXiv preprint (comment: "EMNLP2026 submitted")
- **Link:** <https://arxiv.org/abs/2607.29167>
- **Review depth:** F (PDF; no HTML version exists)
- **Research question:** Does LLM-based memory consolidation rewrite untrusted observations as apparent user history, preserving an action trigger while erasing the low-trust source that should limit its authority?
- **Threat model:** Single-user, two-task setting. In Task A an attacker controls external observations (web pages, email, tool output); in Task B a retrieved consolidated memory may support a high-risk tool call. The attacker cannot write trusted metadata. Platform-maintained provenance, confirmation events, and risk labels are trusted.
- **Methodology:** Formalizes *source-authority non-amplification*: an action-relevant claim inherits no more authority than its least-trusted supporting source. PPMF stores each memory with platform-maintained source, trust, transformation history, risk labels, and an external-derived flag, binds tool-call arguments to supporting memories deterministically, and requires `USER_CONFIRMED` support for side-effecting, purchase, and credential actions. Evaluated with six memory-writer models on synthetic, adaptive, AgentDojo-derived, trace-derived (726 traces), web-sandbox, and BrowseSafe-Bench-derived scenarios.
- **Main findings:** The authors report up to 1.000 ASR for vulnerable consolidated memories and "laundering rates" of 0.958–1.000 even where direct ASR was low. With intact provenance, no unauthorized high-risk action passed the PPMF gate. In a metadata-stress diagnostic, masking 10% or 20% of provenance fields (missing fields default to UNKNOWN) still produced no unauthorized execution, but benign success fell to about 0.887 and 0.814. Forging 10% of confirmations or downgrading 10% of risk labels yielded ASR of about 0.09–0.11.
- **Limitations (stated):** Assumes intact platform provenance, confirmation events, and risk labels. The evaluation focuses on single-agent memory laundering and does not cover multi-tenant shared memory or inter-agent authority transfer. Deletion is not studied.
- **Relationship to MemoryFence:** **The closest prior work on the summarization component and on provenance degradation.** Its metadata stress test shows that *visible* missing provenance fails closed at a utility cost. MemoryFence's distinct question is *silent* edge loss, where a derived memory looks as if it has fewer, possibly only trusted, ancestors. PPMF also gates at execution rather than filtering retrieval, so it maps to MemoryFence's lineage-gated authorization (`DF5`), not to provenance-aware retrieval (`DF2`).

### [Ouyang2026] MemLineage: Lineage-Guided Enforcement for LLM Agent Memory
- **Authors:** Ciyan Ouyang, Rui Hou
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2605.14421>
- **Review depth:** P
- **Research question:** How can useful memory recall be preserved while preventing untrusted-derived state from justifying sensitive actions?
- **Threat model:** Untrusted content written into persistent state re-enters later sessions as an instruction. The paper defines adversary capabilities, non-capabilities, and trust assumptions, and discusses an LLM-inference trust assumption as a limitation.
- **Methodology:** Per-principal signed entries in an RFC 6962 Merkle log. A weighted derivation DAG records which retrieved entries were in context when a new memory was written, with a max-of-strong-edges propagation rule and a sensitive-action gate. **Deletion is non-destructive:** tombstones are appended and the original entry remains provable. Its RQ2 sweeps the lineage threshold against chain lengths of 1, 2, 3, and 5 under several attribution-weight schedules.
- **Main findings:** The authors report zero ASR on a deterministic mechanism-isolation harness and on an AgentDojo banking bridge, with sub-millisecond per-operation overhead. Under a decaying attribution-weight schedule, deeper chains can lose the untrusted label before the chain tip, so the threshold must be chosen jointly with expected chain depth.
- **Limitations (stated):** Soundness depends on attribution edges remaining above threshold; adaptive-adversary coverage is limited; deployment is single-host.
- **Relationship to MemoryFence:** **Strong overlap on lineage-gated defenses and on the interaction of chain depth with attribution quality.** MemoryFence treats MemLineage-style gating as a defense family and measures it end to end with LLM transformations and silently dropped edges, rather than with synthetic weight schedules.

### [Wang2026MAP] MAP-Graph: Provenance-Aware Shared Memory for Multi-Agent Workflows
- **Authors:** Yiqi Wang, Zihao Yan, Jiaqi Zhang, Zhangkai Wu, Mingkai Zheng, Zequn Sun, Yanming Zhu, Taotao Cai
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2608.10509>
- **Review depth:** P
- **Research question:** How can shared memory separate hard authorization from graded trust and adapt evidence requirements to action risk, given that summaries can conceal private, poisoned, untrusted, or revoked sources?
- **Threat model:** Multi-agent workflows in which derived memories may hide restricted ancestry.
- **Methodology:** A typed execution graph over agents, sources, memories, claims, and actions. Permission-ineligible records are excluded, eligible ones are reranked by path trust, and a risk-sensitive gate is applied before actions. On an explicit `revoke_permission` event, affected descendants are **marked, not deleted**. Evaluated on 2,700 synthetic tasks per method across three domains.
- **Main findings:** The authors report strong task success and decision accuracy, that removing the hard permission filter allowed every observed unauthorized read, and that all 450 revoked-source cases were blocked while 41 of 450 action-risk cases were still impermissibly allowed.
- **Limitations (stated):** Synthetic, templated benchmark; simulated actions; one four-agent round per task; single temperature-zero run; baselines are core-mechanism adaptations rather than full reproductions.
- **Relationship to MemoryFence:** **The closest overall prior work.** It already combines derived-memory concealment, revocation, provenance-aware retrieval, and action gating. MemoryFence's defensible additions are deletion handling varied as a factor (MAP-Graph implements one behavior), multi-round transformation depth, lineage capture degraded rather than benchmark-supplied, repeated stochastic runs with uncertainty estimates, and an explicit four-stage outcome funnel.

### [Singh2026] When Does Belief-Based Agent Memory Help? Reliability-Conditional Updating and Provenance-Capped Poisoning Defense
- **Authors:** Pranav Singh
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2606.22030>
- **Review depth:** A
- **Relationship to MemoryFence:** Proposes bounding trust by source provenance rather than textual confidence and reports utility costs. Supports measuring the utility cost of provenance defenses.

### [Sharma2026] SMSR: Certified Defence Against Runtime Memory Poisoning in Persistent LLM Agent Systems
- **Authors:** Tarun Sharma
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2606.12703>
- **Review depth:** A
- **Main findings:** Defines multi-session memory poisoning, in which crafted memories injected through normal channels steer responses *for future users*. Combines HMAC provenance at write time with randomized ablation and voting at query time, and argues that provenance-free retrieval-time filters cannot certify against adaptive injection (per abstract).
- **Relationship to MemoryFence:** Supports the premise that provenance is necessary. Signatures authenticate *who wrote* an entry, not *what a derived entry was derived from*, which is the gap MemoryFence measures.

### [Saidi2026] MutMem: Cryptographically Authorized Mutation in Persistent Agent Memory
- **Authors:** Walid Saidi
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2608.02843>
- **Review depth:** A
- **Relationship to MemoryFence:** Tamper-evident memory mutation. Relevant to the integrity of provenance records, which MemoryFence assumes rather than studies.

## 7. Source deletion and derived-state persistence

### [Yao2026] Forgetting Without Restarting: Execution-State Unlearning for Stateful LLM Agents
- **Authors:** Chao Yao, Yangbo Wei, Zhen Huang, Junhong Qian, Chenle Chen, Shaoqiang Lu, Chen Wu, Lei He
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2609.04875>
- **Review depth:** P
- **Research question:** After a forget request, can an agent behave as if it had never observed the target, given compressed summaries, memory records, plans, and KV cache?
- **Threat model:** Primarily privacy (leakage of revoked information), including adversarial elicitation probes.
- **Methodology:** Models the runtime as a deterministic transition system, proves lower bounds on recomputation, and proposes provenance-guided selective replay. Audited across three agent suites, nine baselines, and three model families.
- **Main findings:** The authors report that deleting a memory record leaves leakage unchanged, that instruction-based forgetting collapses under elicitation, and that source redaction still acted on a revoked preference in 80% of episodes.
- **Relationship to MemoryFence:** **Strong overlap on the deletion premise.** It already shows, in a privacy framing, that source-level deletion is insufficient. MemoryFence treats "source-only deletion leaves derived influence" as an **expected replication**, not a discovery, and focuses on the adversarial-action setting and on comparing deletion policies.

### [Yu2026] From Faulty Memories to Corrected Actions: Dependency-Guided Rollback Repair for Memory-Augmented Agents
- **Authors:** Caili Yu, Yiqi Wang, Jiaqi Zhang, Yiqun Duan, Mingkai Zheng, Zhangkai Wu, Kaize Shi, Taotao Cai
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2608.10502>
- **Review depth:** P
- **Research question:** Given a failed execution and diagnosed faulty memories, can both the answer and the persistent state be recovered while retaining unaffected work?
- **Threat model:** Not adversarial in the MemoryFence sense. Faulty memories (poisoned, stale, or misattributed) are supplied by a diagnosis step.
- **Methodology:** Builds a typed memory-to-action graph from runtime provenance, preserves candidates with independent trusted support, deactivates unsupported state, and selectively replays affected computation. Compares no repair, full memory reset, deleting retrieved memories, MemAudit-style repair, LLM-judge repair, and AgentTrace-style rollback on a 150-case controlled benchmark and a 50-case LongMemEval-V2-derived subset. Memory states are active, deleted, quarantined, or superseded.
- **Main findings:** The abstract states that deleting a source leaves already propagated claims, actions, and derived memories active. The authors report 85.3% recovery versus 77.3% for the best competing method on the controlled benchmark, with full removal of diagnosed faulty memories and preservation of benign memories.
- **Relationship to MemoryFence:** **The closest prior comparison of remediation strategies.** Its "delete retrieved memories" and dependency-guided rollback correspond loosely to MemoryFence's cascade deletion (`DS3`) and cascade with re-derivation (`DS4`). MemoryFence differs in that remediation is triggered by an ordinary source deletion with no diagnosis, reach depends on recorded lineage that may be incomplete, and success is measured by residual unauthorized actions.

### [Xie2026Bemula] Can Agents Forget When Asked? A Benchmark for Memory Unlearning in LLM Agents (Bemula)
- **Authors:** Bofan Xie, Chaokun Wang, Guanchen Ge, Songyao Wang, Fang Niu, Hang Zhang, Wei Wang
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2610.18052>
- **Review depth:** A
- **Main findings:** The authors report that no evaluated memory system passed more than 1.5% of forget requests end to end; systems either leave information extractable or over-delete.
- **Relationship to MemoryFence:** Uses paired control versions of each dialogue, a design MemoryFence adopts (deletion and no-deletion arms on identical episodes).

### [Lin2026] Can Agents Truly Forget? Explore Machine Unlearning for LLM Agents (AUBench)
- **Authors:** Junkai Lin, Ge Xu, Zheng Xu, Junkai Chen, Xiangyuan Lan
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2610.17659>
- **Review depth:** A
- **Relationship to MemoryFence:** Frames agent unlearning across parametric knowledge, persistent memory, and tool acquisition, with provenance-tracked trajectories. Background for the deletion factor.

### [Bourtoule2021] Machine Unlearning
- **Authors:** Lucas Bourtoule, Varun Chandrasekaran, Christopher A. Choquette-Choo, Hengrui Jia, Adelin Travers, Baiwu Zhang, David Lie, Nicolas Papernot
- **Year / venue:** 2021, IEEE Symposium on Security and Privacy
- **Link:** DOI [10.1109/SP40001.2021.00019](https://doi.org/10.1109/SP40001.2021.00019); <https://arxiv.org/abs/1912.03817>
- **Review depth:** A
- **Relationship to MemoryFence:** Foundational argument that removing data requires removing its influence on derived artifacts. MemoryFence applies the analogous concern to derived *memories*, not model parameters.

## 8. Access control, isolation, and runtime authorization

### [Wallace2024] The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions
- **Authors:** Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, Alex Beutel
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2404.13208>
- **Review depth:** A
- **Relationship to MemoryFence:** A model-level defense that assigns privilege by message role. Derived memories may be placed in a role that misrepresents their origin, which is the laundering problem in [Xu2026].

### [Hines2024] Defending Against Indirect Prompt Injection Attacks With Spotlighting
- **Authors:** Keegan Hines, Gary Lopez, Matthew Hall, Federico Zarfati, Yonatan Zunger, Emre Kiciman
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2403.14720>
- **Review depth:** A
- **Relationship to MemoryFence:** Spotlighting (delimiting, datamarking, or encoding untrusted input) is the planned **prompt-level baseline defense**.

### [Chen2025StruQ] StruQ: Defending Against Prompt Injection with Structured Queries
- **Authors:** Sizhe Chen, Julien Piet, Chawin Sitawarin, David Wagner
- **Year / venue:** 2025, USENIX Security Symposium (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2402.06363>
- **Review depth:** A
- **Relationship to MemoryFence:** Model-training defenses are out of scope for implementation but represent the "separate instruction and data channels" approach.

### [Chen2025SecAlign] SecAlign: Defending Against Prompt Injection with Preference Optimization
- **Authors:** Sizhe Chen, Arman Zharmagambetov, Saeed Mahloujifar, Kamalika Chaudhuri, David Wagner, Chuan Guo
- **Year / venue:** 2025, ACM CCS 2025
- **Link:** DOI [10.1145/3719027.3744836](https://doi.org/10.1145/3719027.3744836); <https://arxiv.org/abs/2410.05451>
- **Review depth:** A
- **Relationship to MemoryFence:** As for StruQ. An open-weight SecAlign-trained model could serve as a backend condition.

### [Zhu2025] MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents
- **Authors:** Kaijie Zhu, Xianjun Yang, Jindong Wang, Wenbo Guo, William Yang Wang
- **Year / venue:** 2025, ICML 2025 (per arXiv comment)
- **Link:** <https://arxiv.org/abs/2502.05174>
- **Review depth:** A
- **Relationship to MemoryFence:** Detects attacks by comparing actions under a masked user prompt. An interesting candidate for memory-borne attacks, because retrieval itself depends on the user prompt.

### [Wu2025IsolateGPT] IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems
- **Authors:** Yuhao Wu, Franziska Roesner, Tadayoshi Kohno, Ning Zhang, Umar Iqbal
- **Year / venue:** 2025, NDSS Symposium (arXiv `journal_ref`). The published title is "IsolateGPT: An Execution Isolation Architecture for LLM-Based Systems".
- **Link:** DOI [10.14722/ndss.2025.241131](https://doi.org/10.14722/ndss.2025.241131); <https://arxiv.org/abs/2403.04960>
- **Review depth:** A
- **Relationship to MemoryFence:** Isolation between components is the architectural analogue of per-principal memory isolation.

### [Wu2024IFC] System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective (f-secure)
- **Authors:** Fangzhou Wu, Ethan Cecchetti, Chaowei Xiao
- **Year / venue:** 2024, arXiv preprint
- **Link:** <https://arxiv.org/abs/2409.19091>
- **Review depth:** A
- **Relationship to MemoryFence:** IFC-based planning in which a security monitor keeps untrusted input out of planning. A candidate design for the independent authorization layer.

### [Costa2025] Securing AI Agents with Information-Flow Control (FIDES)
- **Authors:** Manuel Costa, Boris Köpf, Aashish Kolluri, Andrew Paverd, Mark Russinovich, Ahmed Salem, Shruti Tople, Lukas Wutschitz, Santiago Zanella-Béguelin
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2505.23643>
- **Review depth:** A
- **Relationship to MemoryFence:** Tracks confidentiality and integrity labels and enforces policies deterministically. Label propagation through LLM-mediated summarization is exactly where the provenance-completeness question applies.

### [Debenedetti2025] Defeating Prompt Injections by Design (CaMeL)
- **Authors:** Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph Kern, Chongyang Shi, Andreas Terzis, Florian Tramèr
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2503.18813>
- **Review depth:** A
- **Main findings:** Control and data flow are extracted from the trusted query, so untrusted data cannot alter program flow, and capabilities are enforced at tool calls. The authors report solving 77% of AgentDojo tasks with provable security, compared with 84% undefended.
- **Relationship to MemoryFence:** The reference design for **independent action authorization**: enforcement that does not depend on the LLM's judgment. It also quantifies an expected utility cost.

### [Shi2025] Progent: Securing AI Agents with Privilege Control
- **Authors:** Tianneng Shi, Jingxuan He, Zhun Wang, Hongwei Li, Linyu Wu, Wenbo Guo, Dawn Song
- **Year / venue:** 2025, arXiv preprint (the v1 title was "Progent: Programmable Privilege Control for LLM Agents")
- **Link:** <https://arxiv.org/abs/2504.11703>
- **Review depth:** A
- **Relationship to MemoryFence:** Symbolic rules over tool names and arguments, checked deterministically. A concrete template for MemoryFence's action-authorization policy.

### [Kim2025] Prompt Flow Integrity to Prevent Privilege Escalation in LLM Agents
- **Authors:** Juhee Kim, Woohyuk Choi, Byoungyoung Lee
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2503.15547>
- **Review depth:** A
- **Relationship to MemoryFence:** Frames the attack as privilege escalation. MemoryFence's cross-user attack is a confused-deputy escalation in which the attacker borrows the victim agent's privileges.

### [BeurerKellner2025] Design Patterns for Securing LLM Agents against Prompt Injections
- **Authors:** Luca Beurer-Kellner, Beat Buesser, Ana-Maria Creţu, Edoardo Debenedetti, Daniel Dobos, Daniel Fabian, Marc Fischer, David Froelicher, Kathrin Grosse, Daniel Naeff, and four further authors
- **Year / venue:** 2025, arXiv preprint
- **Link:** <https://arxiv.org/abs/2506.08837>
- **Review depth:** A
- **Relationship to MemoryFence:** A catalog of patterns and their security-utility trade-offs, used to classify MemoryFence's defense configurations.

### [Tan2026] MemAudit: Post-hoc Auditing of Poisoned Agent Memory via Causal Attribution and Structural Anomaly Detection
- **Authors:** Zhewen Tan, Yilun Yao, Huiyan Jin, Wenhan Yu, Guoan Wang, Mengyuan Fan, liang lu, Feng Liu, Xiangzheng Zhang, Duohe Ma, Tong Yang, Lin Sun
- **Year / venue:** 2026, arXiv preprint
- **Link:** <https://arxiv.org/abs/2605.23723>
- **Review depth:** A
- **Relationship to MemoryFence:** Post-hoc detection is complementary. It is excluded from the initial defenses but relevant to forensic use of provenance.

## 9. Memory architectures (background)

All entries in this table were reviewed at depth A.

| Key | Title | Authors | Year / venue | Link | Relevance |
|---|---|---|---|---|---|
| [Park2023] | Generative Agents: Interactive Simulacra of Human Behavior | Park, O'Brien, Cai, Morris, Liang, Bernstein | 2023, UIST '23, DOI [10.1145/3586183.3606763](https://doi.org/10.1145/3586183.3606763) | <https://arxiv.org/abs/2304.03442> | Introduces *reflection*, which synthesizes higher-level memories from observations; the model for MemoryFence's reflection transformation. |
| [Packer2023] | MemGPT: Towards LLMs as Operating Systems | Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez | 2023, arXiv | <https://arxiv.org/abs/2310.08560> | Hierarchical memory with LLM-managed paging and summarization. |
| [Zhong2024] | MemoryBank: Enhancing Large Language Models with Long-Term Memory | Zhong, Guo, Gao, Ye, Wang | 2024, AAAI, DOI [10.1609/aaai.v38i17.29946](https://doi.org/10.1609/aaai.v38i17.29946) | <https://arxiv.org/abs/2305.10250> | Memory summarization and forgetting-curve updating. |
| [Chhikara2025] | Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory | Chhikara, Khant, Aryan, Singh, Yadav | 2025, arXiv | <https://arxiv.org/abs/2504.19413> | Production memory layer with LLM-driven extraction and consolidation (add, update, delete). |
| [Wang2025MEXTRA] | Unveiling Privacy Risks in LLM Agent Memory | Wang, He, Zeng, Xiang, Xing, Tang, He | 2025, ACL 2025 Main (per arXiv comment) | <https://arxiv.org/abs/2502.13172> | Memory extraction attacks; the confidentiality counterpart to MemoryFence's integrity focus. |

## 10. Industry disclosures and standards

These are not peer-reviewed research. They establish that the threat class has been observed in deployed systems.

| Source | Publisher / date | Link | Relevance |
|---|---|---|---|
| Spyware Injection Into Your ChatGPT's Long-Term Memory (SpAIware) | J. Rehberger, Embrace The Red, 2024-09-20 | <https://embracethered.com/blog/posts/2024/chatgpt-macos-app-persistent-data-exfiltration/> | Indirect injection that writes persistent instructions into a deployed assistant's long-term memory. |
| Hacking Gemini's Memory with Prompt Injection and Delayed Tool Invocation | J. Rehberger, Embrace The Red, 2025-02-10 | <https://embracethered.com/blog/posts/2025/gemini-memory-persistence-prompt-injection/> | Delayed, trigger-conditioned memory writes. |
| Trust No AI: Prompt Injection Along The CIA Security Triad | J. Rehberger, arXiv 2024 | <https://arxiv.org/abs/2412.06090> | Consolidated catalog of real-world injection findings, including memory persistence. |
| Data Exfiltration from Slack AI via indirect prompt injection | PromptArmor, 2024-08-20 | <https://promptarmor.substack.com/p/data-exfiltration-from-slack-ai-via> | **Cross-user** case: according to the write-up, an attacker posting in a public channel could cause the assistant to exfiltrate data from private channels the attacker was not a member of. |
| CVE-2025-32711 ("AI command injection in M365 Copilot allows an unauthorized attacker to disclose information over a network") | Microsoft; description verified through the NVD API | <https://nvd.nist.gov/vuln/detail/CVE-2025-32711> | Vendor-acknowledged injection vulnerability in an enterprise assistant. |
| GitHub MCP Exploited: Accessing private repositories via MCP | Invariant Labs, 2025-05-26 | <https://invariantlabs.ai/blog/mcp-github-vulnerability> | Untrusted shared content (a public issue) driving an agent to misuse the victim's privileges. |
| OWASP Top 10 for LLM Applications 2025, LLM01: Prompt Injection | OWASP GenAI Security Project | <https://genai.owasp.org/llmrisk/llm01-prompt-injection/> | Standard terminology for direct and indirect injection. |
| Agentic AI: Threats and Mitigations | OWASP GenAI Security Project, 2025-02-17 | <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/> | Lists memory poisoning as an agentic threat category. |
| NIST AI 100-2 E2025, Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations | NIST, 2025-03-24, DOI [10.6028/NIST.AI.100-2e2025](https://doi.org/10.6028/NIST.AI.100-2e2025) | <https://csrc.nist.gov/pubs/ai/100/2/e2025/final> | Authoritative terminology for indirect prompt injection and poisoning. |
| MITRE ATLAS | MITRE | <https://atlas.mitre.org/> | Adversary tactics knowledge base for AI systems. |
| The Dual LLM pattern for building AI assistants that can resist prompt injection | S. Willison, 2023-04-25 | <https://simonwillison.net/2023/Apr/25/dual-llm-pattern/> | Early articulation of privileged/quarantined separation, later formalized by CaMeL. |
| PROV-DM: The PROV Data Model | W3C Recommendation | <https://www.w3.org/TR/prov-dm/> | Vocabulary (entity, activity, agent, `wasDerivedFrom`) that MemoryFence's provenance model adopts. |
| The Protection of Information in Computer Systems | J. H. Saltzer, M. D. Schroeder, Proc. IEEE 1975, DOI [10.1109/PROC.1975.9939](https://doi.org/10.1109/PROC.1975.9939) | — | Least privilege and complete mediation, the principles behind independent action authorization. |
| NIST SP 800-162, Guide to Attribute Based Access Control (ABAC) | NIST | <https://csrc.nist.gov/pubs/sp/800/162/upd2/final> | Reference model for attribute-based authorization decisions. |

The Microsoft whitepaper *Taxonomy of Failure Modes in Agentic AI Systems* (April 2025) reportedly includes a memory-poisoning case study. Its announcement could not be retrieved programmatically, so it is **not verified** for this review and is not relied upon.

## 11. Identified but not yet reviewed

These titles were surfaced by the searches in section 1.1 and verified to exist with the listed title. They appear relevant and must be reviewed before preregistration.

| arXiv ID | Title (as listed on arXiv) | Note |
|---|---|---|
| [2608.01637](https://arxiv.org/abs/2608.01637) | Salami Attack: Stealthy Collusive Memory Poisoning against OpenClaw | |
| [2605.29960](https://arxiv.org/abs/2605.29960) | MemPoison: Bypassing Selective Memory Mechanisms to Plant Backdoors in LLM Agents | arXiv comment: "Accepted by ACM CCS 2026" (not independently verified) |
| [2605.09033](https://arxiv.org/abs/2605.09033) | ShadowMerge: A Novel Poisoning Attack on Graph-Based Agent Memory via Relation-Channel Conflicts | Relevant to merging as a transformation |
| [2609.00523](https://arxiv.org/abs/2609.00523) | Transferable End-to-End Optimization for Indirect Long-Term Memory Poisoning in LLM Agents | |
| [2607.05189](https://arxiv.org/abs/2607.05189) | When Claws Remember but Do Not Tell: Stealthy Memory Injection in Persistent Personal Agents | |
| [2607.28103](https://arxiv.org/abs/2607.28103) | MIND: Lightweight and Effective Memory Injection Defense for LLM Agents via Intent-Aware Information Bottleneck | |
| [2607.19433](https://arxiv.org/abs/2607.19433) | The Chronos Vulnerability: A Taxonomy of Temporal Persistence and Memory-Based Deception in Agentic AI | |
| [2606.10742](https://arxiv.org/abs/2606.10742) | MemVenom: Triggered Poisoning of Multimodal Memories in Web Agents | |
| [2609.17648](https://arxiv.org/abs/2609.17648) | Trust propagation and structural containment in Multi-agent LLM pipelines | |
| [2607.05318](https://arxiv.org/abs/2607.05318) | PiSAs: Benchmarking Contextual Integrity in Multi-User Agentic Systems | |
| [2609.32511](https://arxiv.org/abs/2609.32511) | Learning from Others, Acting for You: Cross-User Memory Sharing for LLM Agents | |
| [2603.20357](https://arxiv.org/abs/2603.20357) | Memory poisoning and secure multi-agent systems | |
| [2605.22842](https://arxiv.org/abs/2605.22842) | The Misattribution Gap: When Memory Poisoning Looks Like Model Failure in Agentic AI Systems | |
| [2603.02240](https://arxiv.org/abs/2603.02240) | SuperLocalMemory: Privacy-Preserving Multi-Agent Memory with Bayesian Trust Defense Against Memory Poisoning | |
| [2609.02265](https://arxiv.org/abs/2609.02265) | CAPTURE: Disentangling Preference Drift from Memory Poisoning in Personalized LLM Agents | |
| [2608.00426](https://arxiv.org/abs/2608.00426) | MAPLE-Guard: Memory-Aware Link Enforcement Against Memory-Link Poisoning in Multi-Agent Systems | Found in the 18 October 2026 refresh; gates memory promotion into shared memory |
| [2609.14976](https://arxiv.org/abs/2609.14976) | MemRiskBench: Trace-Aware Risk-Preserving Evaluation for Long-Horizon LLM Agents | Found in the refresh; includes revoked-memory reuse and cross-user leakage risks |
| [2609.34392](https://arxiv.org/abs/2609.34392) | Org-Agent: Beyond Personal Assistants Towards Organizational Agents | Found in the refresh; organizational authority and attribution constraints |

## 12. Research-gap comparison matrix

Legend: **Yes** = central to the work; **Partial** = present but limited (for example a fixed benchmark field, a single condition, a mechanism-level sweep, or a secondary metric); **No** = absent from what we reviewed; **?** = not determinable at the review depth. These are this review's judgments at the stated depth, not the authors' claims.

| Work | Depth | Cross-principal attacker | LLM-mediated transformation | Source deletion / revocation | Deletion handling varied | Staged outcomes (retrieve / follow / propose / execute) | Provenance-aware retrieval | Independent action authorization | Provenance completeness varied | Repeated runs with uncertainty |
|---|---|---|---|---|---|---|---|---|---|---|
| Greshake2023 | A | Yes | No | No | No | No | No | No | No | ? |
| AgentDojo | A | Yes (third-party data) | No | No | No | No | No | ? | No | ? |
| AgentPoison | A | Partial | No | No | No | ? | No | No | No | ? |
| MINJA | A | Yes | No | No | No | ? | No | No | No | ? |
| MURMUR | P | Yes | No (transcript) | No (attacker cannot delete) | No | Partial | No | No | No | ? |
| Collaborative Memory | A | No (non-adversarial) | Partial (write-time transforms) | Partial (access revocation) | No | No | Yes | No | No | ? |
| Sleeper memory poisoning | A | No (external content, single user) | ? | No | No | Partial (written / retrieved / used) | No | No | No | ? |
| Injection-Execution Dissociation | A | ? | No | No | No | Partial (two stages) | ? | Partial (tool-layer sandbox) | No | Yes |
| PPMF (Provenance Laundering) | F | Partial (external observation, single user) | Yes (consolidation) | No | No | Partial (laundering rate and ASR) | No (gates execution) | Partial (provenance-dependent gate) | Partial (fields masked, visible) | Partial |
| MemLineage | P | Partial (external ancestors) | Partial (derivation DAG; chain length swept) | Partial (tombstones) | No | ? | Yes | Partial (lineage-dependent gate) | Partial (attribution-weight schedules) | ? |
| MAP-Graph | P | Yes | Yes (summaries) | Partial (revocation field) | No | Partial | Yes | Partial (trust-dependent gate) | No (benchmark-supplied) | No (single run) |
| Execution-state unlearning | P | No (privacy) | Yes (compressed summaries) | Yes | Yes (several forget methods) | No | No | No | No | Partial |
| Dependency-guided rollback | P | No (diagnosed faults) | Partial | Yes | Yes (remediation strategies) | No | No | No | No | ? |
| GateMem | P | Yes (multi-principal) | ? | Yes | No | No | Partial | No | No | ? |
| CaMeL / Progent / FIDES | A | Yes (third-party data) | No | No | No | No | No | Yes | No | ? |
| **MemoryFence (proposed)** | — | **Yes** | **Yes, type and depth varied** | **Yes** | **Yes, five policies** | **Yes, four stages** | **Yes** | **Yes** | **Yes, silent edge loss** | **Yes** |

The final row describes **planned** properties of an unbuilt system. It shows the intended contribution, not an accomplished one. Every individual cell for MemoryFence is covered somewhere in prior work. What is proposed as new is their joint, controlled variation, especially deletion handling under incomplete recorded provenance.

## 13. Implications for MemoryFence's design

1. **Reframe the claim.** The contribution is a measurement study and open harness that varies transformation, deletion handling, and recorded-provenance completeness. It is not a discovery of derived-memory persistence.
2. **Replicate before extending.** Include conditions that mirror published settings (raw retrieval with no deletion, as in MINJA- and MURMUR-like setups; intact-provenance gating, as in PPMF- and MAP-Graph-like setups) so results can be checked against prior reports.
3. **Measure the funnel.** Adopt staged metrics and report each stage conditionally and unconditionally, following [Leong2026], [Pulipaka2026], and [Huang2026PMPA].
4. **Distinguish silent from visible provenance loss.** PPMF's fail-closed result under masked fields is the reference point; silent edge loss is the condition MemoryFence adds.
5. **Include benign and legitimate-instruction controls,** following [Yang2026UCC] and [Ren2026], to estimate false positives.
6. **Use deterministic tools and harness-level true provenance** for ground truth, consistent with the mechanism-isolation approach in [Ouyang2026] and the observability caution in [Leong2026b].
7. **Report zero-event cells with upper bounds,** as [Shayoni2026] and [Xu2026] do.
8. **Refresh this review** before the evaluation protocol is frozen.

## 14. Revision notes

This review revises an earlier, unpublished Phase 1 draft. Changes:

- All identifiers were re-verified on 18 October 2026.
- PPMF was read in full. Its matrix row was corrected: it does vary provenance completeness (masked fields), and it gates execution rather than filtering retrieval.
- Dependency-guided rollback was read in part. Its matrix row was corrected to show that it compares remediation strategies.
- MemLineage's chain-length sweep was recorded.
- Four sources from the owner's earlier manuscript were added (MemoryGraft, sleeper memory poisoning, Collaborative Memory, NetInjectBench), as were three newly found titles.
- The "less covered" claims were narrowed accordingly.
