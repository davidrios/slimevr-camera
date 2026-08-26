# TotalCapture access request — email draft (2026-08-26)

Status: drafted, not yet sent. See STATE.md D23 / next action 1.

---

**Subject:** TotalCapture dataset access request — independent open-source research (SlimeVR drift correction)

Dear TotalCapture team / CVSSP Data Manager,

I am writing to request access to the TotalCapture dataset (https://cvssp.org/data/totalcapture/) for a non-commercial research project.

**About the project.** I am working on camera-assisted yaw-drift correction for SlimeVR, an open-source full-body tracking system for VR that uses inexpensive IMU trackers (https://github.com/SlimeVR). Because gravity cannot constrain heading, per-tracker yaw drifts in a motion-dependent way that is hard to model analytically. The project investigates whether one or two cheap cameras plus modern 2D pose estimation can recover each limb's heading during brief still moments and use that as an occasional correction to the IMU orientations. All results, code and write-ups will be published openly.

**Why TotalCapture.** To my knowledge it is the only public dataset that combines raw IMU measurements, multiple static calibrated cameras, and optical (Vicon) ground truth for the same sequences. That combination lets me validate the method offline — injecting synthetic gyro-only yaw drift, using two of the eight views as the "cheap camera pair", and scoring recovered heading against Vicon — before committing to any hardware. Published fusion work (e.g. von Marcard et al., TransPose, PIP, DiffCap) also benchmarks on TotalCapture, which makes it the natural point of comparison.

**My situation, stated up front.** This is an independent, single-person research project, and I am not affiliated with a university or company. I understand the licence normally asks for a signature from a senior representative of an organisation, which I cannot provide. I would nevertheless like to ask whether access can be granted to an individual researcher, and I am happy to sign the agreement personally and to provide any additional information or assurances you find useful. [If public: You can find the project, its documentation and the planned evaluation protocol at <link>.]

**Intended use and commitment to the terms.** My primary intended use is offline evaluation of the method as described above. It is possible that the project would later fine-tune a pose-estimation model on the data and release the resulting weights openly under a non-commercial licence; if you consider that to fall outside the terms, I will restrict use to evaluation only. In all cases I confirm that:

- the video sets and associated data will be used for research purposes only;
- the dataset will not be used for any commercial purpose — the project is open-source and non-commercial;
- the data will not be redistributed in any form; only derived research results (metrics, plots, code that operates on the dataset) will be shared;
- the dataset will be acknowledged in any publication, report or public material that uses it or reports results derived from it, by citing Trumble et al., "Total Capture: 3D Human Pose Estimation Fusing Video and Inertial Sensors" (BMVC 2017) and including the repository link.

Thank you very much for considering this request, and for making the dataset available to the community. I would be glad to answer any questions.

Kind regards,

David Rios Gomes
[city/country]
[email]
[project link, if any]
