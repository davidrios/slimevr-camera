# Conventions for AI sessions in this project

1. **Read `STATE.md` first, always.** Then whichever doc the current task touches. Do not re-derive things already decided there.
2. **This is an us project.** David has domain insight (hardware, SlimeVR internals, VR usage). Ask before choosing between materially different directions; record the answer in `STATE.md`. Prefer a short list of concrete questions over long option surveys.
3. **Ground claims in literature.** Anything from model memory about a paper, model, or accuracy number is a *hypothesis* until a note exists in `literature/`. Write claims as "candidate, unverified" until then. Never invent citations.
4. **Context is finite.** Whenever something is learned or decided, write it to the right file *in the same turn*. Keep `STATE.md` short (< ~150 lines): status, decisions, open questions, next actions. Long material goes in `docs/`, `literature/`, `experiments/`.
5. **Literature notes** use `literature/TEMPLATE.md`. File name `YYYY-firstauthor-shortname.md`. Add a line to `literature/index.md`. Record what we actually checked (abstract only? full read? code run?).
6. **Experiments** are `experiments/NN-short-name/` with a `README.md`: hypothesis, setup, result, conclusion, date. Failed experiments are kept.
7. **Machine**: Linux, 16 cores, 46 GB RAM. GPUs: RTX 3090 24 GB (CUDA — use this for research code) and RX 9060 XT 16 GB (ROCm). David can rent bigger hardware for training if needed.
8. **Python**: 3.12 only (best library support), managed with **uv**. This repo is a uv project (`pyproject.toml`, `src/slimevr_camera/`); run things with `uv run`, add deps with `uv add`. Third-party model repos that need their own env get their own uv project under `tools/<name>/`, never installed into the system Python.
9. Don't commit video to the repo (size, and it is other people's data). Raw video donation from users is acceptable per David (opt-in, HMD anonymizes).
10. **Code map**: `src/slimevr_camera/{skeleton,geometry,heading,pipeline}.py` are the reusable core; `synth/` is synthetic-only. Run tests with `uv run pytest -q tests`. Experiments call the package, never the reverse.
