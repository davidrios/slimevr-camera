# Synthetic human data generators — survey (for agenda §H)

- **Authors / venue / year:** survey note (verified 2026-08-26 by web fetch of repos/pages; "unverified" = page not fetched)
- **Read depth:** READMEs, licence files, project pages; nothing run
- **Date read:** 2026-08-26

## Relevance to us
Which toolchain can render AMASS/generated motion from 1–2 fixed cameras with joint/SMPL-X ground truth, on Linux with the 3090, and let us attach an HMD + controllers to the avatar.

## Candidates
| Tool | Engine / licence | What it gives | Verdict |
|---|---|---|---|
| **XRFeitoria** (openxrlab) | Blender ≥3.0 / Unreal ≥5.1, Apache-2.0 code, PyPI, last push 2025-09 | Python RPC driver; `load_amass_motion` onto SMPL-XL fbx, multi-camera, vertex/joint export (`samples/blender/07_amass.py`) | **best-maintained open toolkit**; no prop-attach API but Blender backend allows bpy parenting |
| **MPI smplx_blender_addon** (gitlab.tuebingen.mpg.de/jtesch) | Blender 4.5+, SMPL-X model licence (NC) | add SMPL-X body, "animated body from AMASS npz", Alembic export | the AMASS→animated body step |
| BEDLAM / BEDLAM 2.0 render tools | Unreal 5.0.3 / 5.3.2 **Windows**, MPI NC (data, code, derived weights) | full pipeline: Blender SMPL-X→Alembic, UE import, MRQ render, camera GT | reference only; NC and Windows |
| SynBody | Unreal via XRFeitoria; data CC BY-NC-SA; SMPL-XL generation code not released | 1.2M images, 1000+ rigged SMPL-XL bodies (FBX) | assets usable NC; re-render via XRFeitoria |
| AGORA | images + SMPL-X fits only, MPI NC | no render pipeline | not for us |
| SURREAL | Blender 2.78, Python 2, NC | obsolete | no |
| BlenderProc | GPL-3, active | generic randomisation (HDRIs, materials, physics, COCO writer); no SMPL pipeline | lighting/scene randomisation layer |
| PeopleSansPeople (Unity) | Apache-2.0 code, Unity 2020 Perception, stale | 28 RenderPeople rigs, COCO keypoints | not SMPL; stale |
| Meshcapade mc-unreal / USMPL / Unity plugin | SMPL NC; login-gated (unverified) | SMPL in engines | NC |
| Infinigen | BSD-3 | scenes only, **no humans** | scene backgrounds at most |
| Isaac Sim Replicator Agent | NVIDIA licence | people + skeleton annotator | heavy, not SMPL |
| Microsoft SynthMoCap | data only (RUDA, NC), generator not released | SynthBody 20k identities | reference recipe |
| UnrealPose(-Gen) 2026 | UE5; official repo unverified | 3D joints, COCO 2D w/ occlusion flags | unverified |
| LiCamPose SyncHuman | MIT, Unity 2021, Windows | multi-cam RGB+LiDAR generator | Windows |

## HMD wearers
No generator or dataset renders an HMD/controllers on the avatar from *external* cameras (UnrealEgo, Ego4View-Syn, EgoPoseVR, SimXR-synthetic are egocentric). Real third-person sets with a headset: EgoBody (HoloLens2, 3–5 Kinects, CC BY-NC-SA), SimXR (Quest 2 + third-person, pseudo-GT, no licence), Ego-Exo4D / EgoHumans (Aria glasses), Nymeria. **Genuine gap.**

## Recommendation
Blender on Linux: smplx_blender_addon (AMASS npz → animated SMPL-X) + XRFeitoria or plain bpy for multi-camera rendering and joint/SMPL-X export; parent our own CC0 HMD + controller meshes to head/wrist bones via bpy; randomise lighting/scenes with BlenderProc + Poly Haven HDRIs (CC0). Skip Unreal unless BEDLAM-grade cloth is needed. Licence: SMPL-X + AMASS make any trained weights non-commercial unless the motion is re-fit from permissive sources (CMU/ACCAD/DanceDB/HDM05) onto a non-SMPL body.
