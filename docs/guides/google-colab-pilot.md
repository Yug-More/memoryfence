# Free Colab pilot

This guide runs the four-cell MemoryFence development pilot on a free Google Colab runtime. The model is downloaded there, not onto your computer. You do not need an API key, a paid Colab plan, or Ollama installed locally.

The pilot is exploratory. It is not a confirmatory study, and it does not establish an attack rate or a defense effect.

## What you need

- A Google account that can open [Google Colab](https://colab.research.google.com/).
- A free runtime. Do not change the runtime to a paid option.
- About 30 minutes of uninterrupted time. Free sessions can end early, and a GPU may be unavailable. The pilot is allowed to run on CPU.

The notebook is [`notebooks/memoryfence_colab_pilot.ipynb`](../../notebooks/memoryfence_colab_pilot.ipynb). The default is the explicitly separate schema-constrained
[`configs/ollama-schema-pilot.json`](../../configs/ollama-schema-pilot.json).
Set SCHEMA_OUTPUT=False to retain the historical native-output configuration
[`configs/ollama-pilot.json`](../../configs/ollama-pilot.json). These conditions must
never be pooled. Real native smoke attempts returned invalid output; this is not
a defense result.

## 1. Open the notebook

After this file is on the `main` branch, open:

https://colab.research.google.com/github/Yug-More/memoryfence/blob/main/notebooks/memoryfence_colab_pilot.ipynb

You can also upload the notebook file from a clone. Use the copy from the commit you intend to run.

## 2. Select a free runtime

Use **Runtime → Change runtime type** and leave the choice on the free CPU or a free GPU if Colab offers one. Do not select a paid runtime. The notebook reads the machine it actually received. A missing GPU is recorded, and the pilot continues on CPU when disk and memory are sufficient.

## 3. Run the cells in order

Use **Runtime → Run all**, or run each cell from top to bottom. Do not skip the setup cells. The sections are:

1. Introduction.
2. Runtime diagnostics, which print Python, memory, disk, CPU, and later the GPU check.
3. Repository setup. The default revision is `main`, which is not a frozen revision. To repeat an exact commit, set `FROZEN = True` and set `REVISION` to the 40-character SHA. A frozen run does not fall back to `main`.
4. Ollama installation (including the official Ubuntu zstd extraction prerequisite). The daemon listens on `127.0.0.1:11434` inside the Colab runtime.
5. Model selection. The only download is `qwen2.5:0.5b`, and only after the disk and memory check passes.
6. Backend smoke test.
7. Experiment preview.
8. The four-cell pilot.
9. A short interpretation that labels the run as exploratory.
10. Artifact export.

The notebook stops if it is not running inside Colab, so opening the file on your computer does not download a model.

## 4. Recognize a successful installation

The Ollama cell prints a line of the form `ollama <version> at http://127.0.0.1:11434`.

The smoke cell then prints:

- `model doctor` with exit status 0
- `model list` including `qwen2.5:0.5b`
- `model smoke` with exit status 0
- a model digest from the local daemon
- `prose_rejected error.model_output`

If the small model cannot return the structured decision, smoke exits non-zero and the pilot does not start. That is a capability limit of this tag. It is not a defense result. Do not switch the tag to a larger model in this notebook.

## 5. Run the pilot

With either output condition, the preview must report four valid cells: `clean-note` and `direct-note`, each with `DF0` and `DF1`. Transformations stay scripted. The victim agent is Ollama. Held-out scenarios are not included.

The run cell calls `memoryfence experiment run`, then `summarize`, then `audit`. `audit` checks the saved files and does not call the model again.

## 6. Inspect the outcomes

Read `report.md` in the printed output. Keep these outcomes separate:

- S1 retrieved
- S2 followed
- S3 proposed
- S4 executed

An abstention is not instruction following. A proposal that authorization blocks is not an execution. Invalid cells stay invalid. The report's counts are the pilot record. They are not a generalizable attack rate. `qwen2.5:0.5b` is not evidence about larger agents.

## 7. Download the results

The last cell writes a zip named `memoryfence-colab-pilot-ollama-pilot-<commit>-<timestamp>.zip` and starts a browser download. The archive contains the configuration, manifest, matrix, run records, summary, report, benchmark results, and `environment.json`.

Confirm the cell prints the archive path and a non-zero size. Keep the file outside the Colab session.

`SAVE_TO_DRIVE = False` is intentional. Drive is not mounted. Change that flag only if you mean to choose a folder yourself. The notebook does not publish the archive.

## 8. If Colab disconnects

Unsaved files on the Colab disk are gone. If the zip already downloaded, keep that zip. It is the record of the run. If it did not download, the run is incomplete and is not a result. Start a new session rather than treating a partial directory as finished.

## 9. Run again without mixing trials

Each run creates a new directory from a UTC timestamp. Do not point a new run at an old directory. Resume is only for the same session, when `config.json` is still there and you choose resume instead of a new run. A new session after a disconnect starts over.

To repeat a configuration, set `FROZEN = True` and the same full commit SHA. Ollama text can still differ between runs. The manifest records the model digest, seed, and generation settings. Identical text is not required.

## 10. What this pilot does not show

- It does not show that an attack works, or that a defense works, outside these four development cells.
- It does not use the held-out templates.
- It does not revise the confirmatory hypotheses.
- It does not validate the judge with a second human rater.
- It does not make `qwen2.5:0.5b` a stand-in for a larger model.
- Free Colab resources can be refused or withdrawn. That is an infrastructure limit, not an experimental outcome.

Scripted experiments on your own computer stay available and do not need this notebook. See [development.md](../development.md).

## Interpreter isolation and output conditions

The live Colab kernel used Python 3.13 while the locked project environment used
3.12. Importing the environment's compiled packages into the kernel failed. Project
steps now run in fresh subprocesses of `.venv/bin/python`; JSON state connects the
steps, and the kernel only handles orchestration and the final download. A regression
test executes this boundary, checks every cell's Python syntax, and preserves state
on subprocess failure.

`agent-v2-json-schema` uses Ollama's explicit JSON-schema output constraint, retaining
the same model, native tool descriptions, trust instructions and strict parser. It
adds explicit field instructions and a response schema. This changes the condition,
so it has separate configurations, hashes and prompt metadata. It does not strip
code fences, repair model prose into actions, or establish task correctness.
The original `agent-v1` outputs and failures remain separate. The schema-mode smoke
uses the planned 2048-token context and 256-token generation limit; the historical
smoke's 256-token context is too small for the full tool prompt in this runtime.
The matched behavioral configuration is `configs/ollama-ticket-schema-pilot.json`;
it must be invoked separately after the four-cell compatibility pilot is inspected.
