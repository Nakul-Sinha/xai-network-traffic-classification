# 05 - Distilled Research Gaps: Explainable AI for Network Traffic Classification

**Provenance.** Distilled from deep-read notes across 13 batches: 78 papers, 70 read in full text
(exceptions and retrieval caveats listed at the end). Ground-truth-usage census across all papers
read, by strongest GT category used for explanation evaluation:

| GT category | count |
|---|---|
| none | 50 |
| synthetic | 9 |
| human_expert | 8 |
| architectural | 5 |
| interventional | 5 |
| other | 1 |

**Headline finding.** 50/78 papers evaluate explanations with *no* ground truth of any kind, and
every genuine ground-truth construction in the corpus (synthetic injection, transparent-by-construction
models, interventional bug/edit pairs) lives in vision, NLP, or synthetic graphs. Not one has been
instantiated on network traffic. The field's flagship survey (Nascita et al., COMST 2024) certifies
this independently: of 107 XAI-for-NTA papers only 5 use any explanation-quality metric, the 17
metric definitions found are mutually inconsistent, and none of its 51 cataloged datasets carries
explanation ground truth - while its own "Coherence" property presupposes exactly such ground truth.

**Verdict key.** *Solo* = solvable by one researcher with public data and modest compute (no testbed,
no paid data, no institutional panel). *ML layer* = sits at the ML/DL layer applied to computer
networks (vs. protocol engineering, HCI, or systems work). *Risk* = risk the gap is already solved
somewhere, with the nearest known prior work named.

---

## Theme A - Ground-truth validation of explanations (top priority)

### G1. No injected-shortcut (synthetic) ground-truth benchmark for NTC explanations

**Gap.** The most transplantable GT recipe in the literature - inject a known discriminative
artifact into the data, reassign labels, verify behaviorally (twin-model / background-only accuracy
tests) that the model uses it, then score explainers on recovering it - exists for images (Zhou et
al. AAAI'22 ~69% attribution mass for the best method; BAM; Debugging Tests) and text (Bastings et
al. EMNLP'22, precision@k on planted lexical shortcuts), but has **never been built for any traffic
representation** (payload bytes, packet-size/timing sequences, tabular flow features, byte-PMI
graphs). Zhou et al. claim domain generality and explicitly do not instantiate it beyond
images/text; Bastings et al. limit themselves to English binary text classification.

**Evidence.** Batch 10 (BAM, Debugging Tests: "no published traffic analogue" of the construction
primitives); Batch 11 (Zhou et al.: "the most directly transplantable ground-truth recipe for NTC
XAI"); Batch 12 (Bastings et al. + Geirhos: "whether saliency can find shortcuts... is entirely open
for network traffic"); Batch 2 (SoK catalogues backdoor-trigger GT, "never ported to traffic");
Batch 5 (COMST survey: zero GT-annotated datasets; open challenge explicitly calls for them).

**What a solution looks like.** A public benchmark: ISCX/CICIDS-class data + injection operators at
three granularities (byte watermarks in payload, forced packet-size/timing signatures, planted flow-
feature values), label reassignment, behavioral verification protocol, and leaderboard-style scoring
(attribution mass / precision@k / mean rank) for SHAP, IG, LIME, attention, GNN explainers.

- **Solo:** yes - public datasets, small models (1D-CNN, RF, small transformer), single-GPU scale.
- **ML layer:** yes.
- **Effort:** 3-5 months for benchmark + first evaluation paper.
- **Risk already solved:** low-to-medium. Nearest work: ShortcutCatcher (CoNEXT/Proc. ACM Netw.
  2026) and BiasSeeker plant/hunt shortcuts but use XAI only as an *unvalidated ranking heuristic*
  and never invert the construction to score explainers; PoliTO Pcap-Encoder documents natural
  shortcuts but scores no explainer. Watch for concurrent work from the PoliTO group - this is the
  fastest-moving adjacent lane.

### G2. No architectural (transparent-by-construction) ground truth over traffic-like data

**Gap.** The strictest GT category - models whose true decision basis is known exactly - exists as
SENECA synthetic transparent classifiers (Guidotti 2021, generic tabular), the single-feature biased
classifier of Fooling-LIME/SHAP, and OpenXAI's LR-coefficient GT (which saturates: three gradient
methods all at 1.000). No NTC/NIDS paper instantiates architectural GT on traffic-like feature
spaces (bounded counts, heavy-tailed durations, correlated multicollinear features, discrete byte
alphabets). The one NTC attempt, LEXNet, is circular: its own prototypes are declared "faithful by
definition" and post hoc methods are scored against them on the train set.

**Evidence.** Batch 12 (Guidotti/SENECA: "no NTC/NIDS paper instantiates architectural GT on
traffic-like feature spaces"); Batch 0 (Fooling-LIME/SHAP template "never applied to traffic
classifiers"); Batch 8 (OpenXAI saturation, tabular-only); Batch 3 (LEXNet circularity); Batch 5
(Kitsune's correlation-clustered per-AE RMSE subspaces are an unexploited *built-in* attribution
mechanism - a free architectural GT candidate).

**What a solution looks like.** A SENECA-style generator parameterized by traffic feature
distributions + a set of known-decision-basis models at increasing realism (linear → tree → planted-
feature CNN on bytes), used to (a) score explainers where truth is exact and (b) calibrate the proxy
metrics of G5 against exact truth.

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-4 months.
- **Risk:** low. Guidotti's code is public but tabular-generic; no traffic instantiation exists.
  (Caveat: Guidotti 2021 full text was unobtainable this session - pull before citing; see caveats.)

### G3. Documented dataset artifacts never used as a real-data recovery benchmark ("tank test")

**Gap.** The corpus contains a ready-made list of *known, documented* decision-basis artifacts in
real datasets: CICIDS2017 TCP-appendix flows (25.9% of flows, Engelen et al.) with the
corrected-vs-original dataset pair; implicit flow-ID bytes SeqNo/AckNo/TCP-timestamps and
checksum-offloading artifacts (Pcap-Encoder: randomizing them collapses ET-BERT 97.4→19.5);
PCAP-metadata and port biases in the "ALL" input (Aceto et al., found by manual ablation); nPrint's
Nmap open-port shortcut; Lucid's IP-flag 0x4000 split. Nobody has ever scored whether popular
explainers *recover* these artifacts on models verified (interventionally) to use them. This is
real-data, domain-realistic ground truth - cheaper and more ecologically valid than G1's injection.

**Evidence.** Batch 2 (Engelen: corrected/original pair "could serve as recovery benchmarks");
Batch 1 (Pcap-Encoder interventions confirm shortcut use; "both papers use XAI only as an
unvalidated ranking heuristic and never invert the construction to score explainers"); Batch 6
(Aceto's known byte locations = "real-data ground truth against which traffic-XAI faithfulness could
be tested - unexploited"); Batch 9 (Sommer & Paxson's tank anecdote and orthogonal-mechanism
doctrine, never operationalized for XAI).

- **Solo:** yes - all datasets public, interventional verification is test-time randomization plus
  cheap retraining. **ML layer:** yes. **Effort:** 2-3 months; combines naturally with G1 into one
  benchmark paper.
- **Risk:** low. No paper in 78 does this; closest (Trustee tampering, netUnicorn loop) are one-off
  diagnostics, not explainer scoring.

---

## Theme B - Causal / interventional faithfulness (top priority)

### G4. No faithfulness protocol valid for discrete, protocol-constrained traffic inputs

**Gap.** Every deletion/insertion/occlusion metric NTC papers import (RISE deletion, AOPC,
Warnecke's Descriptive Accuracy, ERASER comprehensiveness/sufficiency) embeds removal semantics that
break for traffic: zero is a valid byte, blur is undefined for packets, nullified fields yield
protocol-grammar-invalid flows, and the OOD confound (ROAR) is *worse* off-manifold than for images.
The two fixes - retraining-based ROAR and ROAD's noisy linear imputation - are respectively
compute-prohibitive-and-pixel-centric and intrinsically image-specific (relies on pixel neighborhood
structure). No protocol-valid, minimally-class-revealing imputation operator exists for packets or
flows; no one has tested whether NTC method rankings survive a change of removal operator (Samek's
own appendix shows ABPC swinging 113.75-243.69 with the scheme). Networking also possesses a
*unique* interventional handle no other XAI domain has - replaying grammar-valid modified packets
against the classifier - which nobody has turned into a faithfulness protocol.

**Evidence.** Batch 0 (ROAR never adapted to discrete packet/flow inputs); Batch 11 (ROAD:
fixed-value/zero masking - the NTC default - is the provably worst imputation; "no protocol-valid,
minimally-revealing imputation operator exists... to enable a 'traffic-ROAD'"); Batch 6 (removal
baselines undefined for traffic; RISE fill strategy chosen because it "gives higher scores");
Batch 9 (Samek operator dependence; LEMNA's OOD deduction tests); Batch 5 (replay-modified-packets
identified as networking's unique interventional handle, unexploited).

**What a solution looks like.** Define grammar-aware removal/imputation operators per representation
(header-field resampling from empirical marginals, payload re-encryption, size/timing jitter within
protocol bounds); a "traffic-ROAD" fidelity curve; an operator-sensitivity audit showing which
published NTC rankings flip.

- **Solo:** yes - ROAD-style (no retraining) keeps compute modest; scoped ROAR on small models is
  feasible. **ML layer:** yes. **Effort:** 3-5 months.
- **Risk:** low. ROAD authors flag the image-specificity themselves; no traffic port exists in the
  corpus or its citation neighborhoods.

### G5. Faithfulness *metrics* themselves never meta-evaluated in NTC (causal diagnosticity)

**Gap.** The field evaluates explainers with metrics that have themselves never been validated -
an infinite regress the corpus documents explicitly (Hedstrom's sMPRT/eMPRT validated by yet another
consistency proxy; Quantus shows one parameter flips rankings; Tomsett shows Krippendorff alpha <
0.48 and MoRF/LeRF reversals for the exact metric family NTC imports). Zaman & Srivastava (EMNLP'25)
provide the remedy - *diagnosticity*: score each metric by the probability it ranks a known-faithful
explanation above a known-unfaithful one, constructed via model editing - and find popular metrics
at chance. This meta-evaluation has never been run for any traffic model, metric, or representation,
even though the traffic versions add an extra confound (deleted flow features create impossible
flows).

**Evidence.** Batch 12 (Zaman & Srivastava; "metric meta-evaluation is entirely absent in NTC, where
deletion/descriptive-accuracy metrics are conventioned, not validated"); Batch 4 (sMPRT/eMPRT
infinite regress); Batch 6 (Quantus parameter flips; "meta-evaluation is absent everywhere");
Batch 1 (Tomsett reliability failures + "nobody has run these reliability sanity checks on NTC
saliency metrics").

**What a solution looks like.** Construct faithful/unfaithful explanation pairs on traffic models
(via G1/G3 planted-shortcut models, where the faithful explanation is known), compute diagnosticity
of Descriptive Accuracy, deletion-AUC, LFR, fidelity, sparsity, stability across operators; publish
which metrics are usable in NTC and under what conditions.

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-4 months on top of G1/G3 infrastructure.
- **Risk:** low. Zaman & Srivastava is NLP-only and brand new; nothing adjacent in networking.

### G6. Sanity-check and reliability batteries never ported to traffic models

**Gap.** The necessary-condition falsification batteries - model-parameter and data randomization
(Adebayo), input invariance (Kindermans), adversarial/permuted attention (Jain & Wallace),
infidelity/max-sensitivity (Yeh) - have never been run on any NTC model class (byte transformers,
1D-CNNs, autoencoder NIDS, traffic GNNs). This is not a mechanical port: the Captum study shows
image conclusions do not transfer to text (SSIM has no analogue for byte matrices; conclusions are
modality-dependent), and Yona/Greenfeld show the randomization check is task-confounded. Meanwhile
NTC papers display attention heatmaps and bit-level importances as explanations with zero
falsification applied, and downstream work cites axiom-passing as if it certified faithfulness.

**Evidence.** Batch 1 (Sanity Checks image-specific; "porting the[m]" open); Batch 5 (Captum
modality-dependence; batteries "never been run on traffic representations"); Batch 4
(Yona/Greenfeld task-confounding; sMPRT variants untested outside vision); Batch 7 (Kindermans'
"inspection-impossible domains" paradox makes traffic the extreme case).

- **Solo:** yes - reuse public NTC checkpoints/architectures, retrain small models on permuted
  labels. **ML layer:** yes. **Effort:** 2-3 months; strong first paper / thesis chapter.
- **Risk:** low-to-medium. It is the most obvious port on this list, so a scoop is conceivable, but
  nothing surfaced across 78 papers or the survey's 107.

---

## Theme C - Explanation redundancy and multiplicity (priority)

### G7. The disagreement problem is unquantified on traffic, where it should be worst

**Gap.** Krishna et al.'s six disagreement metrics show explainers conflict pervasively (negative
rank correlations on tabular NNs; IG-vs-SmoothGrad pixel correlation 0.001) - but with no security
practitioners and no network data. The one measured NTC datapoint (SoK: 25.5% SHAP/LIME top-3
disagreement on NetFlows) has no arbiter because no ground truth exists. Traffic feature spaces are
heavily multicollinear (the multicollinearity-fragility paper; Kitsune's damped-window correlated
features), which should *aggravate* disagreement - unmeasured. Worse, inter-method agreement is used
*as* validation in NTC (Wang et al. 2020's 73% "coincidence rate" with a decision tree), a practice
Neely et al. formally reject (mean Kendall-tau 0.27; agreement is not evaluation).

**Evidence.** Batch 9 (Krishna: no networking data, no security practitioners); Batch 2 (SoK 25.5%
figure); Batch 12 (Neely; "directly undercuts a still-common NIDS/NTC validation practice");
Batch 10 (Wang coincidence rate); Batch 3 (multicollinearity fragility, single dataset).

**What a solution looks like.** Port the six metrics to NTC explainers across representations,
stratify disagreement by feature-correlation structure, then - uniquely - *resolve* it against
G1/G3 ground truth: when methods disagree, which one is right, and does agreement predict
correctness at all?

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-3 months.
- **Risk:** medium for the descriptive half (disagreement studies are fashionable; someone may run
  the port); low for the GT-anchored resolution half, which requires Theme-A machinery nobody has.

### G8. Redundancy makes single-explanation evaluation ill-posed; fidelity ≠ completeness

**Gap.** Trustee's own experiment proves the point the field ignores: a 3-node decision tree with
*perfect* F1 fidelity to the black box failed the tampering test - removing exactly its three
explained bytes left black-box accuracy unchanged, because alternative shortcuts existed. ROAR's
authors flag the same failure mode (fully redundant features defeat removal metrics); BiasSeeker
finds occlusion sometimes *improves* accuracy. Traffic data is saturated with redundant
encodings of the same signal (flow-ID in SeqNo *and* AckNo *and* TCP-TS; size visible in multiple
counters). No NTC evaluation accounts for multiplicity: an explainer pointing at a *different but
equally sufficient* decision basis is scored as unfaithful, and a surrogate covering one basis is
certified while others remain. No Rashomon-set / multiple-sufficient-subset enumeration exists for
traffic models.

**Evidence.** Batch 3 (Trustee fidelity-completeness failure, stated near-verbatim; BiasSeeker
occlusion paradox); Batch 0 (ROAR redundancy caveat); Batch 1 (SeqNo/AckNo/TCP-TS redundant
shortcut family); Batch 12 (Neely: agreement metrics "conflate explanation multiplicity with
error - no[t] disentangled").

**What a solution looks like.** Define explanation evaluation over *sets* of sufficient decision
bases: enumerate minimal sufficient feature subsets via iterated interventional removal + retraining
on small traffic models; score explainers on coverage of the set, not match to one element; show
which published fidelity numbers are inflated or deflated by redundancy.

- **Solo:** partly - the concept and small-model instantiation are solo-feasible; exhaustive
  enumeration on deep byte models is compute-heavy and needs scoping to flow-feature models.
- **ML layer:** yes. **Effort:** 4-6 months.
- **Risk:** low. Rashomon literature exists in interpretable-ML theory but no traffic or security
  instantiation appeared anywhere in the corpus.

---

## Theme D - Dataset artifacts × explanations (priority)

### G9. Explanations of models trained on artifact-ridden benchmarks are unfalsifiable in-lab

**Gap.** The dominant XAI-NIDS pipeline explains models trained on CICIDS2017/NSL-KDD/DARPA-lineage
data where (a) up to 25.9% of flows are pipeline artifacts, (b) labels descend from never-validated
synthetic generation (McHugh; Mahoney & Chan: a one-byte TTL detector matches top 1999 systems), and
(c) shortcut features genuinely predict in-lab. Consequence, drawn by nobody in the applied
literature: *proxy metrics reward explanations that faithfully point at artifacts, and plausibility
checks are confounded because the wrong features really are predictive.* Lucid celebrates what look
like dataset shortcuts as correct learning; E-XAI/nPrint/DeepAID evaluate explanations on exactly
these datasets with no artifact control. No paper systematically re-audits published XAI-NIDS
findings on corrected datasets, though the corrected-vs-original CICIDS2017 pair makes this a
controlled experiment sitting in public.

**Evidence.** Batch 2 (Engelen + "proxy metrics reward explanations that faithfully point at
artifacts"); Batch 8 (McHugh: two unvalidated layers compound); Batch 7 (Mahoney & Chan); Batch 9
(Lucid's "confirmations" as shortcut celebration); Batch 4 (Arp et al.: lab datasets yield
plausible-looking "signatures" from shortcut models).

**What a solution looks like.** Re-run 3-4 published XAI-NIDS analyses on original vs corrected
CICIDS2017 (and artifact-randomized variants); quantify how much of each published explanation's
mass sits on documented artifacts; propose an artifact-disclosure protocol for XAI-NTC papers.

- **Solo:** yes - everything public. **ML layer:** yes. **Effort:** 2-3 months.
- **Risk:** low. Dataset critiques exist; the *interaction* with explanation evaluation is claimed
  by no one in 78 papers.

### G10. NTC input representations are attribution-hostile and nobody audits them

**Gap.** Representation choices made for accuracy silently destroy attributability, and no paper
audits this axis: TFE-GNN collapses all identical byte values into one graph node (per-position
attribution impossible *by construction*); ET-BERT/PERT bigram hex tokens are semantically opaque to
analysts; byte-to-grayscale-image reshaping (Wang 2017 lineage) imports 2D-locality assumptions
saliency methods rely on but traffic lacks; and the per-packet vs per-flow unit-of-analysis question
(McHugh's unresolved "unit of analysis") determines what an attribution can even mean. Downstream
saliency work inherits these choices unexamined - every SHAP map on a byte-image is conditioned on
an accuracy-motivated representation never designed to be explained.

**Evidence.** Batch 11 (TFE-GNN "structurally hostile to attribution"; FlowPic sold on
interpretability, never validated); Batch 0 (ET-BERT opaque bigram tokens); Batch 8 (Wang 2017
representation origin; McHugh unit-of-analysis); Batch 1 (YaTC's MFR retains header rows containing
known shortcut fields).

**What a solution looks like.** A taxonomy + measurable criteria of "attributability" per NTC
representation (position-preservation, semantic addressability, granularity alignment), applied to
the 8-10 dominant encodings; paired demonstrations of the same underlying flow explained under
attribution-friendly vs hostile encodings.

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-3 months; strong survey-paper section even
  without new experiments.
- **Risk:** low. No prior articulation found anywhere in the corpus.

---

## Theme E - Drift × explanations (priority)

### G11. No temporal-drift-aware explanation evaluation exists

**Gap.** TESSERACT shows classifier F1 collapses (0.97→0.32) under realistic temporal splits - so
explanations computed on randomly-split models (the NTC default: ET-BERT, FS-Net, Deep Packet, YaTC
all use random splits) explain artifacts of temporally biased training. No analogue of TESSERACT's
AUT exists for explanations: no metric for explanation stability/validity over time, no faithfulness
notion for *explanation deltas* under drift. The two systems that do explain drift validate only by
narrative or self-referential proxy: INSOMNIA checks that permutation-importance shifts match domain
expectations (Idle Max rises when Slowloris appears - post-hoc plausibility storytelling); CADE's
headline "fidelity" is the very quantity its explainer optimizes, with 1-sample expert anecdotes as
semantic validation. The COMST survey independently flags incremental-training XAI as an open
challenge beyond current tools.

**Evidence.** Batch 0 (TESSERACT; "no metric like an 'AUT for explanation stability over time'
exists"); Batch 12 (INSOMNIA as "canonical instance of the pattern the survey targets"); Batch 1
(CADE self-referential fidelity, 1.41% boundary-crossing unremarked); Batch 5 (COMST incremental
challenge); Batch 12 (proposed transfer: "define faithfulness for temporal explanation deltas under
drift").

**What a solution looks like.** An "AUT-for-explanations": evaluate explainers on temporally split
public longitudinal data (CESNET datasets are public and span months), measure (a) explanation drift
vs model drift vs data drift, (b) whether drifted explanations remain faithful (via G4 operators),
(c) whether explanation deltas predict which classes degrade - the last giving explanations
*predictive* validity under drift.

- **Solo:** yes - CESNET/ISCX-longitudinal public; modest compute. **ML layer:** yes.
- **Effort:** 3-5 months. **Risk:** low. Named as open by two independent sources in-corpus; nobody
  has claimed it.

---

## Theme F - Plausibility vs faithfulness (priority)

### G12. NTC systematically conflates plausibility with faithfulness; no domain formalization exists

**Gap.** Jacovi & Goldberg's axiom - human/expert agreement measures plausibility, never
faithfulness - is violated by essentially every applied NTC evaluation in the corpus: Lucid's
narrative confirmation, nPrint's p0f/Nmap folklore cross-checks, DeepAID's 2-3 hand-picked case
tables, Wang 2020's attack-characteristics table, Kalakoti et al.'s global SOC-analyst 5-feature
mask applied to *local* explanations (plus impossible RMA sigmas up to 25 on a [0,1] metric). The
conflation is uniquely dangerous in NTC because of G9: wrong features are genuinely predictive
in-lab, so plausible ≠ faithful *and* implausible ≠ wrong. Meanwhile the field discards its one
usable plausibility instrument: Mahoney & Chan's 2003 per-attack feature-"legitimacy" rubric
(fraction-legitimate as a metric) is a never-adopted template for *scored, multi-rater* expert
plausibility evaluation, properly labeled as plausibility. ERASER shows the two axes can coexist in
one benchmark with separated metric families; NTC has neither axis operationalized.

**Evidence.** Batch 6 (Jacovi & Goldberg; "consequence for NTC, drawn by nobody"); Batch 2
(Kalakoti flaws; informal plausibility everywhere; SoK: cherry-picking-prone); Batch 7 (Mahoney &
Chan rubric "ready-made, never-adopted"); Batch 9 (LEMNA golden-rule matching "anecdotal", proposed
as scored benchmark).

**What a solution looks like.** A two-axis evaluation protocol for NTC: faithfulness via Theme A/B
ground truth; plausibility via a modernized, multi-rater legitimacy rubric over protocol semantics
(fields with RFC-defined meaning give traffic an objective advantage over images here - Tomsett's
abandoned rule-generated GT failed for images but protocol grammar is rule-generated by nature).
Report the two scores separately and measure their (dis)association empirically.

- **Solo:** partly - the formalization, faithfulness axis, and rubric construction are solo-feasible
  using RFCs and attack documentation; credible multi-rater scoring needs 3-5 domain colleagues
  (cheap, but not literally one person). **ML layer:** yes. **Effort:** 3-4 months.
- **Risk:** low. The distinction is canonical in NLP; its NTC operationalization appears nowhere.

### G13. Analyst-grounded human evaluation is absent exactly where analysts are the justification

**Gap.** Every applied paper motivates itself by operator/SOC-analyst trust; none measures it. SoK:
user studies in only 14% of security-XAI works, median n=8, none in NTC; EXP-SEC's
analyst-narrative module gets three hand-crafted vignettes, zero measurement; Trustee defers user
studies to future work; Hase & Bansal's controlled simulatability protocol - the best-validated
human instrument - presupposes human-legible features and is structurally unavailable for raw-byte
inputs, and its subjects were undergraduates, not analysts. Debugging Tests' finding that users
rely on predictions and ignore attributions is untested "exactly where it matters most."

**Evidence.** Batch 2 (SoK 14%/n=8); Batch 4 (EXP-SEC vignettes); Batch 3 (Trustee deferral);
Batch 7 (simulatability structural mismatch); Batch 10 (Debugging Tests human result).

- **Solo:** no - human-subjects recruitment of security analysts, IRB/ethics process, and
  compensation exceed the one-researcher/public-data envelope. Feasible later as a collaboration.
- **ML layer:** yes (object of study is ML explanations for network security, though methods are
  HCI). **Effort:** 6-12 months with collaborators.
- **Risk:** low that it gets solved soon (structural barriers affect everyone equally). Keep as a
  stated open problem in the journal paper, not a contribution.

---

## Theme G - Robustness, auditing circularity, and evaluation hygiene

### G14. Adversarial robustness of NTC explainers under protocol-valid perturbation is unstudied

**Gap.** Fooling-LIME/SHAP's scaffolding attack exploits perturbation-based explainers' OOD
sampling - and its authors' key enabling condition (perturbed samples detectably off-manifold) is
*aggravated* in traffic, where perturbed packets are protocol-invalid, yet no attack or defense has
been instantiated against any traffic explainer. The S&P SoK's attack taxonomy contains no traffic
explainer; its certified-robustness results explicitly fail for discrete inputs like bytes.
Ghorbani-style verdict-preserving perturbations that misdirect analyst triage (shift the explanation
while keeping the alert) are an unstudied, operationally severe threat; EXP-SEC itself concedes
perturbation-probing evasion. Robustness is also systematically conflated with correctness (a
certifiably robust explainer can be robustly wrong) - unexamined in NTC.

**Evidence.** Batch 0 (Fooling-LIME/SHAP OOD vulnerability "should be aggravated" for traffic);
Batch 4 (S&P SoK: no traffic explainers, convexity results fail for discrete inputs); Batch 7
(Ghorbani attack + proposed traffic threat model); Batch 4 (EXP-SEC concession).

- **Solo:** yes - attacks are cheap; protocol-valid perturbation operators from G4 are reusable.
- **ML layer:** yes. **Effort:** 3-4 months.
- **Risk:** low-to-medium - adversarial-XAI is an active community; the *protocol-validity*
  constraint and triage threat model are the defensibly novel parts.

### G15. XAI-as-shortcut-auditor is itself unvalidated (the circularity nobody closes)

**Gap.** The community's prescribed remedy for spurious correlations is XAI (Arp et al., pitfall
P4) - but there is no auditor for the auditor. Both existing NTC shortcut-hunting systems
(ShortcutCatcher, BiasSeeker) use explainers as ranking heuristics with *known defects*
(cardinality-biased RF impurity importance over-ranks exactly the max-cardinality shortcut fields;
univariate AMI misses interactions) and validate only downstream (leave-one-out accuracy;
occlusion deltas that sometimes paradoxically improve accuracy). Neither ablates the explainer
against random or mutual-information ranking, so nothing is learned about whether XAI contributes
anything. Vision evidence is discouraging (Zhou: mostly negative on spurious-correlation detection;
Debugging Tests: attributions miss mislabeling) - and untested on traffic.

**Evidence.** Batch 4 (Arp circularity: "unvalidated explainers audit models"); Batch 1
(ShortcutCatcher "replaceable ranking heuristic - no ablation vs random/MI"; Pcap-Encoder
cardinality bias); Batch 3 (BiasSeeker occlusion paradox); Batches 10/11 (Zhou/Debugging Tests
negative results).

**What a solution looks like.** End-to-end benchmark of shortcut-*detection pipelines* (explainer
ranking + confirmation step) against planted shortcuts (G1) and documented artifacts (G3), with
random/MI/frequency baselines - answering "does XAI actually help find shortcuts in traffic, and
which explainer, at what cost?"

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-3 months on Theme-A infrastructure.
- **Risk:** medium - this is the lane ShortcutCatcher/BiasSeeker are in; their next papers could add
  the missing ablation. Mitigation: the GT-anchored framing (score the explainer, not the pipeline)
  remains unclaimed.

### G16. Metric-definition anarchy and statistical malpractice in published XAI-NTC evaluations

**Gap.** The evaluation literature that does exist in NTC is internally broken in auditable ways:
COMST finds 17 metric definitions with the same names and different meanings and only 3 tools
implementing any; Traffic-Explainer's printed Fid/Acc formulas are identical and its C-Fid
definition, as printed, rewards useless explanations while its explainer optimizes nearly the same
masked quantity its metrics measure; Kalakoti et al. report impossible standard deviations;
E-XAI runs significance tests on classifier accuracy rather than XAI metrics; EXP-SEC's "true causal
groups" (Group Bloat Factor) are never operationally defined; single-seed evaluations are the norm
(Bastings: configuration, not method, often determines outcomes - undermining bake-offs at library
defaults). No harmonized definitions, no reporting checklist, no Quantus-equivalent exists for
traffic.

**Evidence.** Batch 5 (COMST 17-definition table); Batch 4 (Traffic-Explainer inconsistencies;
EXP-SEC GBF); Batch 2 (Kalakoti sigmas; E-XAI testing practice); Batch 12 (configuration
sensitivity, single-seed norm).

**What a solution looks like.** A definitional audit + harmonization table (survey contribution), a
statistical-reporting protocol (seeds, CIs, tests on metric distributions), and a small open toolkit
instantiating the harmonized metrics with G4 operators - the "Quantus-for-traffic".

- **Solo:** yes. **ML layer:** yes. **Effort:** 2-3 months; natural backbone section of the journal
  survey itself.
- **Risk:** low. COMST tabulated the inconsistency but fixed nothing; no toolkit exists.

### G17. Behavioral/transfer oracles for explanation validity are unexploited

**Gap.** Explanations make implicit *predictions* - a model relying on transferable semantics
should transfer; one relying on dataset-specific artifacts should not - and networking uniquely has
an aligned same-task cross-dataset framework (the CESNET/Orange "one task" setup) to test them. No
paper uses cross-dataset transfer (or deployment behavior generally) as an oracle for explanation
faithfulness: the "one task" paper does its failure analysis by manual feature statistics while
naming explainability as the bottleneck, and its finding that all datasets should be expected to
contain spurious correlations makes explanation-predicted transfer a falsifiable, GT-free
complement to Theme A. This operationalizes Sommer & Paxson's "orthogonal mechanism" doctrine for
explanations rather than detectors.

**Evidence.** Batch 3 ("one task" paper: aligned framework "an unexploited behavioral oracle for
explanation faithfulness"; explanations "make testable transfer predictions"); Batch 9 (Sommer &
Paxson orthogonal-mechanism doctrine, never operationalized for XAI).

**What a solution looks like.** For matched models on two datasets, partition attributed features
into predicted-transferable vs predicted-specific; test whether ablating each partition moves
in-dataset vs cross-dataset accuracy as the explanation predicts; score explainers by predictive
accuracy of their transfer claims.

- **Solo:** yes - CESNET datasets public; Orange replaced by a second public corpus. **ML layer:**
  yes. **Effort:** 3-4 months.
- **Risk:** low. The idea appears only as my own note on the "one task" paper; no citation trail.

---

## Priority ranking for the journal paper

Tier 1 (core novel contributions, all solo-feasible, low risk):
**G1 + G3** (one benchmark paper: injected + documented-artifact ground truth),
**G4** (protocol-valid faithfulness operators / traffic-ROAD),
**G5** (diagnosticity meta-evaluation of NTC metrics),
**G11** (drift-aware explanation evaluation),
**G12** (plausibility/faithfulness two-axis protocol).

Tier 2 (strong supporting contributions): G2, G6, G7 (GT-anchored half), G8, G9, G16.

Tier 3 (frame as open problems or later work): G10 (survey section), G13 (not solo), G14, G15
(scoop risk - move fast or cite-and-frame), G17.

Merge guidance: G1+G3 publish together; G5 and G16 share infrastructure with G4; G15 is the
"application payoff" chapter of the G1/G3 benchmark.

---

## Retrieval caveats (verify before citing)

- **FS-Net**: abstract-only (IEEE 418 on all mirrors). **Wang ICOIN 2017** (malware CNN):
  abstract-only, no OA copy exists. **Keshk et al. 2023** (Inf. Sci.): abstract-only.
  **Kalakoti JIOT 2024**: abstract-only. **Guidotti 2021**: abstract + author code only - pull PDF
  via institutional access before citing its limitations.
- **Wang 1D-CNN (end-to-end)**: html_partial via verbatim abstract + near-complete third-party
  translation, cross-checked with citing surveys.
- **ET-BERT, TESSERACT**: read via ar5iv HTML, not publisher PDF.
- **Batch-0 notes file** (deepread-batch-0.md) was never written (plan-mode blocked writes); temp
  extracts at `corpus/notes/tmp-{deeppacket,roar,foolinglime}.txt`.
- Full notes for other batches: `corpus/notes/deepread-batch-{1,2,4,7,8,10,12}.md`.
