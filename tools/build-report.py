#!/usr/bin/env python3
"""Build the shareable HTML report (docs/figures embedded as data URIs).
Usage: uv run python tools/build-report.py OUT.html"""
from __future__ import annotations
import base64, pathlib, sys
F = pathlib.Path(__file__).resolve().parents[1] / "docs" / "figures"
def img(name, alt):
    b = base64.b64encode((F / name).read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{b}" alt="{alt}"><figcaption>{alt}</figcaption></figure>'
CSS = '''
:root{--bg:#F4F6F8;--surface:#FFFFFF;--ink:#1A222B;--muted:#5F6B78;--rule:#D6DCE2;--cam:#1B7A8C;--imu:#B9741F;--good:#2E7D4F;--goodbg:rgba(46,125,79,.10);--warn:#B3261E;
--serif:"IBM Plex Serif",Georgia,"Times New Roman",serif;--sans:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#101519;--surface:#171E25;--ink:#E4E9EE;--muted:#93A0AC;--rule:#2A333D;--cam:#5FB8C9;--imu:#E0A458;--good:#6FBF8B;--goodbg:rgba(111,191,139,.12);--warn:#F08A82}}
:root[data-theme="dark"]{--bg:#101519;--surface:#171E25;--ink:#E4E9EE;--muted:#93A0AC;--rule:#2A333D;--cam:#5FB8C9;--imu:#E0A458;--good:#6FBF8B;--goodbg:rgba(111,191,139,.12);--warn:#F08A82}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.55;margin:0}
.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 80px}
.col{max-width:68ch}
header{border-bottom:1px solid var(--rule);padding-bottom:20px;margin-bottom:28px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--serif);font-weight:600;font-size:40px;line-height:1.1;margin:8px 0 10px;text-wrap:balance}
h2{font-family:var(--serif);font-weight:600;font-size:26px;margin:44px 0 12px;text-wrap:balance}
p{margin:0 0 14px} .lede{font-size:19px;color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:24px 0 8px}
.stat{background:var(--surface);border:1px solid var(--rule);padding:14px 16px}
.stat .v{font-family:var(--mono);font-size:28px;font-weight:500;font-variant-numeric:tabular-nums;line-height:1.1}
.stat .l{font-size:13px;color:var(--muted);margin-top:6px}
.cam{color:var(--cam)} .imu{color:var(--imu)}
figure{margin:22px 0} figure img{max-width:100%;height:auto;display:block;border:1px solid var(--rule);background:#fff}
figcaption{font-size:13.5px;color:var(--muted);margin-top:8px;max-width:80ch}
table{border-collapse:collapse;font-size:15px;font-variant-numeric:tabular-nums;margin:12px 0 18px}
.tw{overflow-x:auto} th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--rule);vertical-align:top} th{font-weight:600;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
td.n{font-family:var(--mono)}
.ok{background:var(--goodbg)} .bad{color:var(--warn);font-weight:500}
ul,ol{padding-left:22px;margin:0 0 14px} li{margin-bottom:6px}
code{font-family:var(--mono);font-size:.9em}
.finding{border-left:3px solid var(--cam);padding:2px 0 2px 16px;margin:18px 0}
.finding.imu{border-left-color:var(--imu);color:inherit}
.finding b{display:block;margin-bottom:4px}
.note{font-size:14px;color:var(--muted)}
a{color:var(--cam)} a:focus-visible{outline:2px solid var(--cam);outline-offset:2px}
'''
html = f'''<title>SlimeVR Camera Correction</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
<div class="eyebrow">slimevr-camera · sessions 1–2 · 2026-08-26/27 · David Rios & Claude</div>
<h1>Camera-assisted drift correction for SlimeVR trackers</h1>
<p class="lede col">Can one or two cheap cameras fix the drift of IMU trackers? After two sessions the answer has a shape: not by correcting arbitrary motion, but by performing an <em>automatic full reset</em> whenever the camera sees the user in a pose it learned while the trackers were still trustworthy — standing, or seated and relaxed.</p>
<div class="stats">
<div class="stat"><div class="v imu">0.4 %</div><div class="l">gyro scale-factor error per turn (drift-lab), plus unpredictable motion-driven drift; static drift &lt; 1 °/h</div></div>
<div class="stat"><div class="v cam">5–13°</div><div class="l">heading error of off-the-shelf detectors after 1-s averaging (chest → thighs), MoVi, 5 subjects, 3 detectors — model size irrelevant</div></div>
<div class="stat"><div class="v cam">~2°</div><div class="l">residual within one pose family — the bias is repeatable, hence learnable in the post-reset window</div></div>
<div class="stat"><div class="v">1–4°</div><div class="l">chest and feet in seated / idle poses with no calibration at all — inside the 5° budget today</div></div>
</div>
</header>

<div class="col">
<h2>1 · Problem and framing</h2>
<p>SlimeVR trackers report orientation only; positions come from forward kinematics, so a bone's yaw error is the position error of everything below it — 10° at the hip is about 15 cm at the feet. Pitch and roll are anchored by gravity; yaw is pure gyro integration.</p>
<p>David's drift-lab (2026-08-25) settled what the drift is: <span class="imu">not a bias</span> — static drift is under 1 °/hour because the firmware nulls it at rest — but a <span class="imu">gyro scale-factor error</span> (+0.43 % and −0.23 % on two units, opposite signs) together with unpredictable error that appears under modest movement. Accelerometer bias also drifts thermally, tilting pitch/roll by 0.8–5.7 °/hour, and straps slip — which is why yaw-only resets leave visible drift in other directions.</p>
<p>So the tracker is treated as a black box, and two complementary truths are used instead: the <span class="imu">IMU body model is trusted for a short window after a full reset in a known pose</span>; the <span class="cam">camera is drift-free but biased</span>. The post-reset window calibrates the camera; the corrected camera then holds the trackers until the next reset. Periodic user resets bound the horizon.</p>
<div class="finding imu"><b>Product shape: an automatic full reset in familiar poses.</b> Nothing is corrected during arbitrary motion. Whenever the camera sees the user in a pose it learned while the IMU was trusted — the standing reset pose, or the user's seated relaxed idle — it performs the equivalent of a full reset: pelvis, chest and feet headings plus bone directions are measured (a full 3-DoF offset per tracker), and thighs/shins follow the same pose assumption the manual reset already makes. Heavy activity is followed by a manual reset, as today; the user is an active participant and may be prompted. Success means the manual-reset horizon under everyday movement grows from minutes to a session — and no more standing up straight to reset while seated.</div>
<p>Target v1: 5° on long bones. Setup: SteamVR + Quest 3 + 11 BNO085 trackers.</p>

<h2>2 · What the literature says</h2>
<p class="note">31 verified notes, five syntheses in <code>docs/04-lit-synthesis.md</code>. Only papers with a note are cited.</p>
<ul>
<li><b>Nobody has shipped camera-corrects-IMU-yaw.</b> The precedent is VIP (von Marcard 2018): solving one heading per IMU accounts for most of the IMU+video fusion gain, which validates the per-tracker framing.</li>
<li><b>Body-model regressors are too imprecise in rotation</b> (22–25° per joint on EMDB; twist unreliable). So we estimate 3D joints and derive headings geometrically.</li>
<li><b>Calibration from people alone reaches 0.5–2°</b>; the headset trajectory fixes scale and position. Calibration is not the bottleneck.</li>
<li><b>The IMU-only literature never fixes global yaw</b> — the one online method (TIC 2025) says so explicitly.</li>
<li><b>SlimeVR PR #1805</b> (jabberrock) already does a one-shot phone-camera yaw + mounting fit. Reference only; the right integration slot is the Stay Aligned yaw hook in <code>Tracker.kt:300</code>.</li>
<li><b>Data:</b> TotalCapture (requested), Fit3D, and MoVi (open download) have marker truth with static cameras. No public set has headset wearers — that has to come from synthetic renders and our own recordings.</li>
</ul>

<h2>3 · Synthetic harness (experiments 01–02)</h2>
<p>A small package (<code>src/slimevr_camera/</code>) implements the whole loop on synthetic data: skeleton, cameras, triangulation, heading estimators, stillness gate, correction. Two formulation results carried straight into the real data:</p>
<div class="finding"><b>A vertical bone's yaw is unobservable from its own endpoints.</b> A standing shin projects to a point on the floor. Yaw has to come from lateral features — hip width, shoulder width, heel→toe, the knee or elbow flexion plane. Seated poses, with bent knees, are <em>easier</em> for the camera.</div>
<div class="finding"><b>Compare the same physical axis on both sides.</b> Drift rotates the floor projection of every bone axis equally, so the camera may observe any convenient axis and the IMU computes that same axis. A naive "forward axis" comparison hid a 12–14° systematic error.</div>
</div>
{img("exp01_noise3.png","Experiment 01 — injected motion-dependent drift (top) and the corrected error (bottom) at 3 px keypoint noise; grey bands are still windows.")}
<div class="col">
<p>With white pixel noise, in-window heading error stays under 2° even at 10 px. Experiment 02 (revised after David objected to a "net turning" conclusion) models the unpredictable part as a motion-driven random walk: residual grows with √(gross motion since the last correction); learning a per-unit scale factor fits noise and was dropped.</p>
</div>
{img("exp02_mrw005_2min.png","Experiment 02 — motion-driven random walk σm = 0.05 °/√°, still window every ~2 min: reset-only (top) vs reset plus a learned scale factor (bottom). No gain.")}

<div class="col">
<h2>4 · A real detector on real video (experiment 04, MoVi)</h2>
<p>MoVi provides two hardware-synced, calibrated 800×600 cameras about 4.5 m from the subject — our deployment geometry — plus Qualisys marker truth with Visual3D <em>segment frames</em>: true per-bone orientation. The loader was verified end to end (calibration by reprojection; segment forward kinematics to 1–5 mm against joint centres). The reference for each tracker is the fixed local axis of its segment that our estimator observes — what a perfectly mounted IMU would report. Errors are reset-referenced: the per-subject median is removed, since a full reset absorbs a constant offset. Five subjects, three detectors (RTMPose-m; RTMPose-x body; RTMPose-x wholebody with toes), run on the 3090.</p>
</div>
{img("fig_overlay.png","Subject 1, frame 1000. Green: marker joint centres reprojected through the verified calibration. Red: RTMPose-x wholebody. The detector's hips sit above and outside the joint centres — the bias is visible by eye.")}
{img("fig_bones_body-balanced.png","Five subjects, RTMPose-m: heading error after 1-second averaging, per bone. The green band is the 5° budget.")}
<div class="col">
<div class="tw"><table>
<tr><th>bone</th><th>RTMPose-m</th><th>RTMPose-x body</th><th>RTMPose-x wholebody</th><th>verdict</th></tr>
<tr><td>foot L / R (still)</td><td class="n">—</td><td class="n">—</td><td class="n">MAE 1.9 / 1.6°</td><td class="ok">best source</td></tr>
<tr><td>chest</td><td class="n">5.1°</td><td class="n">5.1°</td><td class="n">5.2°</td><td>borderline</td></tr>
<tr><td>hip</td><td class="n">7.5°</td><td class="n">7.0°</td><td class="n">7.2°</td><td class="bad">misses</td></tr>
<tr><td>shin L / R</td><td class="n">8.0 / 9.6°</td><td class="n">7.9 / 10.0°</td><td class="n">8.3 / 10.1°</td><td>borderline</td></tr>
<tr><td>thigh L / R</td><td class="n">12.5 / 12.9°</td><td class="n">13.2 / 13.5°</td><td class="n">12.5 / 12.9°</td><td class="bad">misses</td></tr>
</table></div>
<p class="note">sd of the 1-second mean heading error, all motions, 5 subjects.</p>
</div>
{img("fig_timeline_body-balanced_s1.png","Subject 1 over its 21 motions: the error is slowly varying and pose-dependent (thigh −30° during cross-legged sitting), not white noise.")}
{img("fig_yaw_body-balanced.png","Error versus the body's yaw relative to the camera pair: the bias depends on viewing direction.")}
{img("fig_models.png","RTMPose-m versus RTMPose-x wholebody on subjects 1–2: a larger backbone does not reduce the heading error. The 5-subject runs agree.")}
<div class="col">
<div class="finding"><b>The detector's heading error is not noise.</b> Thirty-frame averaging barely reduces it (per-frame sd 6–14° → 5–11°). It is pose- and view-dependent.</div>
<div class="finding"><b>Model size does not help.</b> Three detectors agree within noise on every bone: the error is structural to where detectors place joints.</div>
<div class="finding"><b>Feet and chest are the reliable heading sources; thighs the worst.</b> Heel→toe is a long, nearly horizontal, well-seen axis. Upper arms cannot be evaluated on MoVi — its arm frame has no stable twist.</div>
</div>
{img("fig_seated.png","Seated and idle-like motions, 5 subjects, wholebody detector, no calibration: chest and feet are inside the budget; hips need the per-pose calibration; cross-legged sitting hides feet and knees and is the hardest seated pose.")}
<div class="col">
<h2>4b · Can the post-reset window calibrate the detector? (experiment 05)</h2>
<p>David's proposal, tested on the same data. A constant or yaw-binned offset learned in the first 30–60 s does not transfer to the other twenty motions. But within one pose family the error is nearly constant — first half of each motion → second half leaves a residual sd of:</p>
<div class="tw"><table>
<tr><th>bone</th><th>uncorrected sd</th><th>within-pose residual sd</th></tr>
<tr><td>chest</td><td class="n">5.4°</td><td class="n ok">1.8°</td></tr>
<tr><td>hip</td><td class="n">8.5°</td><td class="n ok">2.1°</td></tr>
<tr><td>shin L / R</td><td class="n">7.6 / 6.5°</td><td class="n ok">2.6 / 1.9°</td></tr>
<tr><td>thigh L / R</td><td class="n">12.5 / 9.3°</td><td class="n">5.3 / 1.9°</td></tr>
</table></div>
<div class="finding"><b>The bias is a repeatable function of pose and view — learnable, but only with a pose-conditioned model.</b> Learned globally by fine-tuning on diverse data, refined per session in the trusted post-reset window. The corollary became the product shape: correct in poses the trusted window already saw, where the residual is ~2° today.</div>
<p class="note">Caveats throughout: 5 subjects; 800×600 at 4.5 m is a pessimistic setup; MoVi motions are 3–8 s, a weak proxy for a VR session where the same idle poses recur for minutes; calibration is perfect.</p>

<h2>5 · Infrastructure</h2>
<ul>
<li>Local machine: data and analysis; datasets on <code>/mnt/data2</code>. GPU box <code>vulcanus</code> (RTX 3090): 45–65 fps RTMPose with a CUDA-12 onnxruntime declared in <code>pyproject</code>; 250 GB ext4 image on <code>/mnt/slimevr-data</code>; reproducible via <code>tools/vulcanus-setup.sh</code>.</li>
<li>MoVi pilot (5 subjects, both views, three detector variants) cached on both machines; verified loader in <code>slimevr_camera.data.movi</code>; evaluation in <code>experiments/04-movi-detector-bias/evaluate.py</code>.</li>
<li>uv-managed Python 3.12 project; tests; experiment folders with READMEs; <code>STATE.md</code> with decisions D1–D33; this report is built by <code>tools/build-report.py</code>.</li>
</ul>

<h2>6 · Open threads</h2>
<ul>
<li>TotalCapture access (requested); Fit3D as backup.</li>
<li>Synthetic-pipeline synthesis (Blender + SMPL-X add-on + XRFeitoria, own headset meshes) and BEDLAM licence terms — agent pending.</li>
<li>Optional experiment 03 (on-body drift with known-pose returns); RTSP camera model.</li>
</ul>

<h2>7 · Next steps</h2>
<ol>
<li><b>Build the automatic full reset in familiar poses.</b> Familiar-pose detector (templates from the manual reset and the seated/idle stances, learned while trusted); in-pose measurement of pelvis, chest and feet headings and bone directions; application through the full-reset path; confidence → prompt. Evaluate on MoVi still stances, then on our own recordings.</li>
<li><b>Own-room dataset:</b> two RTSP cameras + 11 trackers + Quest 3, with the ESP32 coded-blink beacon for sync. This is where recurring idle poses exist.</li>
<li><b>Pose-conditioned correction model:</b> global fine-tuning on MoVi / TotalCapture / synthetic-with-headset data, refined per session.</li>
<li><b>Runtime scheduler:</b> per-unit drift statistics from successive corrections; bone weighting by measured reliability.</li>
</ol>
</div>
</div>
'''
out = pathlib.Path(sys.argv[1]); out.write_text(html); print(out, f"{out.stat().st_size/1e6:.1f} MB")
