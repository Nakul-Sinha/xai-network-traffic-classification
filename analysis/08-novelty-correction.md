# Novelty correction - READ THIS BEFORE WRITING THE INTRO

I nearly overclaimed. Correcting now, from full-text reads.

## Ground-truth-based evaluation of attribution is NOT new. It is established in three modalities.

| modality | work | how ground truth is manufactured | headline finding |
|---|---|---|---|
| Vision | **BAM/BIM** - Yang & Kim (Google Brain), 2019 | *Paste* an object into every image of a class; relative importance is known a priori ("a pasted gray square must matter less than the region it covers") | attribution methods produce **"false positive explanations - features that are incorrectly attributed as more important"** |
| Vision | CLEVR-XAI, 2021 | synthetic scenes; ground-truth object masks | ranking of methods differs from proxy-metric ranking |
| NLP | **Bastings, Ebert, Zablotskaia, Sandholm, Filippova - EMNLP 2022** | *Inject* a lexical shortcut token with p=0.25; verify the model learned it (100% on synthetic test set vs chance for a control model); ask whether salience finds it | "some of the most popular method configurations provide poor results **even for simple shortcuts**" |
| Tabular | OpenXAI, 2022 | synthetic generators with known ground truth | - |
| **Network traffic** | **NOTHING** | - | - |

**So my Track A is Bastings' protocol ported to packets.** I must cite it as the direct methodological
ancestor and say so plainly. Claiming to invent ground-truth XAI evaluation would be false and a
reviewer would kill the paper on sight.

## What IS defensibly novel

### N1. The modality has never been done - and it is the modality where the method works best.
Not a gap-filling exercise for its own sake. Four concrete reasons networking is strictly better
than text or vision as a substrate for this protocol:

1. **Interventions are on-manifold.** Pasting a dog into a photo makes an unnatural photo; injecting
   `#0` into a sentence makes unnatural text. Rewriting a packet's TTL and recomputing the checksum
   produces **an ordinary, valid packet** that a real host could have sent. The single biggest
   objection to perturbation-based ground truth simply does not apply here.
2. **The feature space has a published grammar.** Byte k *is* a named protocol field. Attribution can
   be scored at byte, field, header and layer granularity with a mapping that is standardised
   (RFCs), not annotated. Text has tokens; vision has pixels; neither has a grammar.
3. **Real, documented, consequential artifacts already exist.** Bastings must *invent* shortcuts.
   I can ALSO use natural ones whose causal role is already established in the literature -
   ISCX Ethernet-header misalignment (TRUSTEE §7.2), CIC-IDS-2017 TTL 64 vs 128, CICFlowMeter TCP
   appendices, SII (MAC/IP/port) whose occlusion drops ET-BERT 0.96 -> 0.51. Ecological validity
   that a purely synthetic protocol cannot claim.
4. **Graded ground truth, not binary.** Bastings verify reliance with a binary check (synthetic test
   accuracy 100% vs chance). Packet rewriting supports *graded* per-field necessity N(F) and
   sufficiency S(F) measured on the original distribution - a continuous reference, not a flag.

### N2. Redundancy-aware ground truth - genuinely new in ANY modality
Every precedent injects ONE shortcut and asks "is it found?". None asks whether the model holds
**several mutually substitutable** shortcut sets, which would make the target of attribution
*non-unique* and the whole exercise ill-posed rather than merely inaccurate.

Networking is where that question became visible: TRUSTEE Table 3 - destroy the three bytes a
perfect-fidelity (F1=1.00) surrogate named, and accuracy is unchanged (0.959 -> 0.959), because
"the black-box model succeeds in finding alternative shortcuts." ShortcutCatcher (Proc. ACM Netw.
2026) independently needs an *iterative* removal loop, which is indirect evidence of the same thing.
Vourganas & Michala (2026) prove collinear features inflate attribution variance - the statistical
shadow of the same phenomenon - but measure only explainer variance, never model-level multiplicity.

**R(M) = number of disjoint sufficient field sets** is, as far as the corpus shows, unmeasured
anywhere. That is the paper's most original contribution and it generalises beyond networking.

### N3. Stakes: this modality has live downstream consumers
xNIDS (USENIX Sec'23) emits *active defence rules* from explanations. ShortcutCatcher *deletes
features* based on them. EXP-SEC pipes them to analysts. NIDS-dataset surveys *prescribe* XAI as the
artifact-audit instrument. In vision, a wrong saliency map mislabels a demo figure; here it changes
a firewall rule. Nobody has checked the instrument.

## Revised claim, safe to defend
> "Ground-truth evaluation of feature attribution has been established in vision (Yang & Kim 2019)
> and text (Bastings et al. 2022) but never in network traffic - the one modality where the
> intervention that defines the ground truth is exact, on-manifold, and protocol-structured. We port
> the protocol, extend it from binary shortcut-recovery to graded interventional necessity, and add
> a redundancy-aware notion of ground truth that reveals a failure mode - non-unique explanation
> targets - that single-shortcut protocols in any modality cannot see."

## Consequence for the experimental design (04)
Add a mandatory baseline: reproduce Bastings-style **binary** shortcut recovery first, so my graded
and redundancy-aware measures are shown to add information over the established protocol, not merely
to restate it in a new domain.

---

# CORRECTION 2 - the on-manifold packet intervention is NOT mine to claim

From the full text of **Traffic-Explainer** (Ponraj, Durairajan, Wang; arXiv 2509.18007, Sep 2025),
§ global-class evaluation. I had read the abstract only and misjudged this paper. Verbatim:

> "We perform a byte-swapping experiment across traffic sequences occurring at different country
> locations. Specifically, we swap the top 10% most important bytes, identified by Traffic-Explainer,
> between traffic flows belonging to different countries and examine how this affects the output of
> various classifiers, including Transformer, ET-Bert, and MLP ... this manipulation consistently
> causes the classifiers to change their predictions toward the target country"

and - this is the sentence that pre-empts my "on-manifold" argument almost word for word:

> "our byte-swapping operation involves exchanging 16-bit hex values between two valid sequences, so
> **the checksums remain correct, and the network traffic is still valid in the real world** after
> swapping bytes."

**So: packet-level, checksum-correct, on-manifold intervention on traffic classifiers already exists
in print.** I must cite it as the direct precedent and drop any claim to inventing it. That is now
the second overclaim this project has walked back, both caught by reading full text rather than
abstracts.

## What survives, stated precisely

The difference is **the direction of inference**, and it is not cosmetic.

| | Traffic-Explainer | this proposal |
|---|---|---|
| role of the intervention | **confirmatory** - validates bytes *its own* explainer nominated | **constitutive** - builds an independent reference, then audits all explainers against it |
| which features get intervened on | only the explainer's top-10% | every protocol field, systematically |
| what is measurable | sufficiency of the nominated set | necessity **and** sufficiency, graded, per field |
| blind spots | structurally invisible - bytes the method missed are never swapped | **blind-spot rate** is a primary metric |
| redundancy | not asked | **R(M)** = number of disjoint sufficient sets |
| explainers compared under intervention | one (theirs) | full matrix: SHAP/IG/DeepLIFT/LIME/occlusion/attention |
| artifacts used | one task (country localisation), synthetic swap | + natural documented artifacts (TRUSTEE, TTL, SII, TCP appendices) |
| proxy metrics | Fid/Acc/C-Fid/C-Acc reported *as* the evaluation | proxies **meta-evaluated** against the interventional reference (RQ3) |

A confirmatory test can only ever return "yes". Swapping the bytes your method chose and seeing the
label move shows the chosen set is *sufficient*; it cannot show that a **disjoint** set is equally
sufficient - which is precisely the TRUSTEE Table 3 phenomenon (tamper the named bytes, accuracy
unchanged at 0.959, because alternative shortcuts exist). Traffic-Explainer's design cannot see that
failure mode, and reports 42% improvement on proxy metrics that the same phenomenon can satisfy.

## Revised framing - stronger, not weaker
The old framing ("nobody intervenes on packets") was **false**. The true framing is sharper:

> The network community already possesses the right instrument - Ponraj et al. demonstrated that
> checksum-preserving byte interventions are exact, on-manifold and transferable across models. It
> has only ever been pointed at explanations the authors already believed. Nobody has turned it
> around and used it as an *independent reference* to audit the explainers the field actually
> deploys, or asked whether the reference it defines is even unique.

## Also corrected: LEXNet is quantitative, not qualitative
Earlier I recorded LEXNet's faithfulness check as a single-sample figure. The deep-read pulled the
numbers: post-hoc recovery of the model's true (by-construction) prototypes is **Grad-CAM 8.2% /
38.9%** and **SHAP 5.9% / 27.4%** on top-protos / top-10-regions, versus 100% for the by-design
explanation. That is a real, quantitative ground-truth result showing post-hoc attribution recovering
under 10% of what the model provably used - and it is strong supporting evidence for RQ1, on the one
architecture where such ground truth was available. Cite it as motivation, not as a competitor.
