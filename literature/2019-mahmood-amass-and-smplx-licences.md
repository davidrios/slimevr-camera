# AMASS (Mahmood et al. 2019) and SMPL / SMPL-X model licences — what a public-weights release may use

- **Authors / venue / year:** Mahmood, Ghorbani, Troje, Pons-Moll, Black — ICCV 2019 (AMASS). SMPL-X: Pavlakos et al., CVPR 2019. This note is about **licences**, not method.
- **Link:** https://amass.is.tue.mpg.de/ ; licence https://amass.is.tue.mpg.de/license.html ; per-sub-dataset pages `https://download.is.tue.mpg.de/amass/licences/<name>.html` ; SMPL-X https://smpl-x.is.tue.mpg.de/modellicense.html ; SMPL https://smpl.is.tue.mpg.de/modellicense.html
- **Code:** `smplx` Python package (https://github.com/vchoutas/smplx) — its LICENSE is the **same MPI non-commercial licence**, not MIT. CPU-capable (PyTorch).
- **Read depth:** licence pages read (fetched 2026-08-26); AMASS download page itself is login-gated, not fetched.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

AMASS is the motion source for any BEDLAM-style pipeline and SMPL-X is the body used to render it. Both carry MPI non-commercial terms that propagate to trained weights; this note records exactly which text applies and which sub-datasets are permissive at the source.

## What they do (licence terms, quoted)

**AMASS umbrella licence**: "To use the Dataset for the sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects." "Any other use, in particular any use for commercial purposes, is prohibited." "This license also prohibits the use of the Dataset to train methods/algorithms/neural networks/etc. for commercial use of any kind." No redistribution ("shall not be copied, shared, distributed, re-sold ... or sub-licensed"). Nothing addresses releasing trained weights explicitly — only the *purpose* of training is restricted. This umbrella applies to the SMPL-H/SMPL-X **fits** of every sub-dataset, including the permissive ones.

**Sub-datasets** (from the AMASS licence pages):

| Sub-dataset | Licence | Content |
|---|---|---|
| CMU | "free for all uses ... may include this data in commercially-sold products" (mocap.cs.cmu.edu); AMASS page attribution only | dance, sports, arm-heavy |
| ACCAD | CC Attribution (no NC; version not stated) | martial arts, gestures |
| DanceDB | CC BY-SA 3.0 US | dance |
| HDM05 | CC BY-SA | sports, dance-like |
| BMLmovi, BMLrub | BioMotionLab custom NC, forbids commercial training | everyday/sports |
| MoSh, PosePrior, DFaust, GRAB, SOMA, MOYO, Transitions, SSM | MPI NC licence | GRAB hand-object, MOYO yoga |
| KIT | AMASS page: citation only; KIT's own terms **unverified** | whole-body |
| SFU, TotalCapture, EKUT, HumanEva, WEIZMANN, CNRS, EyesJapan, TCDHands, HUMAN4D | licence text missing/404 on AMASS pages — **unverified** | HUMAN4D is VR-oriented |

**SMPL-X model licence**: "sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects"; "Any other use, in particular any use for commercial, pornographic, military, or surveillance, purposes is prohibited"; "may not be used to train methods/algorithms/neural networks/etc. for commercial, pornographic, military, surveillance, or defamatory use of any kind." SMPL adds "prohibits the use of the Software to train ... for commercial use of any kind." Commercial route: Meshcapade / smpl@max-planck-innovation.de (Meshcapade pages returned 403, pricing unverified).

## Key numbers (with table/figure reference)

Not applicable (licence note). AMASS: 15 sub-datasets at release, >40 h mocap, SMPL-H fits (SMPL-X fits added later).

## What we can reuse / what to be careful about

- **For a non-commercial open-source release**: AMASS + SMPL-X are usable as-is; the resulting weights must be labelled non-commercial (e.g. CC BY-NC) and the renders/AMASS npz cannot be redistributed. Precedent: 4D-Humans and WHAM ship MIT weights trained on AMASS/SMPL without addressing this; MMHuman3D flags that such weights inherit SMPL terms; VPoser (trained on AMASS) is MPI-NC. Community practice ≠ licence text; no enforcement found. Legally untested.
- **For fully open (commercial-OK) weights**: use only the source data of CMU / ACCAD / DanceDB / HDM05 (re-fit from original C3D/BVH with our own skeleton or a non-SMPL body, e.g. a rigged character), because the AMASS SMPL-X fits re-wrap them in MPI terms. Or obtain written permission (ps-license@tue.mpg.de).
- The `smplx` package itself is NC — a permissive-weights pipeline would need to avoid SMPL-X entirely at render time (e.g. MakeHuman/Mixamo/MetaHuman bodies driven by retargeted BVH).
- SlimeVR shipping a consumer model: if any commercial use is foreseen, NC data is a hard blocker; decide this before building the pipeline (question for David, record in STATE.md).

## Open questions this raises

- Sub-dataset terms marked unverified above (SFU, TotalCapture, KIT, HUMAN4D...).
- Would MPI grant written permission for an open-source, non-profit consumer release? Only answerable by asking.
- Is a non-SMPL rigged body acceptable for our GT (we need joints + head pose, not mesh)?
