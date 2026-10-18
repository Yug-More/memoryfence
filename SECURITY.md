# Security Policy

MemoryFence studies attacks on AI agent memory so that defenses can be evaluated. This document covers how to report vulnerabilities and the boundaries for responsible use.

## Supported versions

MemoryFence is pre-release (`0.1.0.dev0`). Only the latest commit on `main` is supported.

## Reporting a vulnerability

**In MemoryFence itself** (for example, a bug that lets harness code reach the network, leak credentials, or let a defense read ground truth):

- If GitHub's **private vulnerability reporting** is enabled for this repository, use it: open the "Security" tab and choose "Report a vulnerability".
- If it is not enabled, open a public issue that says only that you have a security report and asks for a private channel. **Do not include vulnerability details in public issues.**

Include the affected commit, reproduction steps, and the impact you observed. This is an independent project with no guaranteed response time; reports will be acknowledged as soon as practical.

**In a third-party product**, discovered while using MemoryFence techniques: report it to that vendor through its official disclosure channel first, and allow a reasonable remediation period before publishing. Do not file details in this repository.

## Responsible-use boundaries

MemoryFence is intended for **defensive research in controlled environments**.

- **Simulated execution only.** Harness tools are code-defined simulations with no external side effects. Do not connect them to real email, chat, storage, or payment systems.
- **Synthetic data only.** Users, documents, and credentials in scenarios are fictional. Do not add real personal data.
- **Inert payloads.** Recipient identifiers use the reserved `.invalid` top-level domain (RFC 2606), so payloads cannot reach a real destination.
- **No unauthorized testing.** Do not use this project or its scenarios against systems, accounts, or data you do not own or are not explicitly authorized to test.
- **No production-targeted tuning.** Contributions must not include attacks optimized against named production systems.

## Handling of secrets

- Phase 1 requires no credentials.
- In later phases, optional hosted-model credentials are read only from environment variables, never committed, and never written to logs.
- `.env` files are git-ignored, and the pre-commit configuration includes a private-key detector.
