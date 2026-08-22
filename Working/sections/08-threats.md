# 8. Threats to validity

**Resampling changes the joint distribution.** PacketDO preserves each field's marginal but, by
sampling it independently of the label, alters its joint distribution with the other fields. A model
that relied on a genuine correlation between two fields would register a necessity drop that is real
but not attributable to either field alone. We mitigate this in three ways: interventions resample
class-agnostically from real values (so every counterfactual is a value the field actually takes); we
report field-set necessity for the documented redundant families, not only single-field necessity;
and we include a null-intervention control field in every table, whose necessity stays within the
noise floor and calibrates what "zero necessity" means for the estimator.

**The model must not be retrained under intervention.** Necessity and sufficiency are properties of a
fixed model; retraining after an intervention (as remove-and-retrain protocols do) measures a
different model and reintroduces the confound our operator was designed to avoid. We freeze the model
for all interventions. Where a strength sweep requires different models, each strength is trained once
before any intervention is applied to it.

**Byte-versus-field granularity.** Byte-level explainers attribute to byte offsets, which we
aggregate to protocol fields using a fixed header-offset map valid for the canonical no-options
layout. Two consequences: attributions to bytes shared by two fields, or to variable-length options,
are aggregated approximately; and where header lengths differ across samples (the misalignment that
motivates protocol-aware parsing) absolute offsets are not stable. We report results at both byte and
field granularity and use protocol-parsed offsets for the misaligned cases.

**Cost of exact methods.** KernelSHAP is orders of magnitude slower than the gradient and tree
methods; we bound it with stratified subsampling and report the measured wall-clock cost, which is
itself a datapoint for line-rate deployment. This means KernelSHAP results are computed on fewer
samples than the other methods, with correspondingly wider uncertainty.

**Occlusion is close to the ground-truth operator.** Occlusion removes a feature by permutation,
structurally similar to PacketDO's resampling. Its strong faithfulness is therefore partly by
construction, and we state this explicitly rather than presenting occlusion as an independent winner.
E5 disentangles the effect by scoring occlusion under both the zero-mask and PacketDO operators.

**Synthetic versus real.** The graded-strength results are on synthetic traffic, where ground truth
is planted and exact. Their external validity rests on the real-data replication (CIC-IDS2017), where
the false-confidence and blind-spot phenomena reproduce on documented natural artifacts; but the real
data is flow-level, so the byte-level artifacts (time-to-live, header misalignment, sequence-number
bytes) that require packet captures are documented and left to a byte-level replication. The
destination-port and flow-construction artifacts we do measure on real data are the ones representable
in flow features.

**Serializer circularity.** Both PacketDO's validity and the validity checker rely on the same
protocol serializer. We harden this in two ways: the checker was cross-validated against a
from-scratch one's-complement (RFC 1071) checksum implementation on adversarial corruptions, and the
operator's per-field correctness is covered by unit tests; an independent validator (e.g. tshark) is a
further step. The E1 macro-validity figure is an unweighted average over synthetic fields, not a
per-packet real-traffic rate, and three fields are valid under zero-masking only because the generator
left them zero; on real traffic the zero-mask validity would if anything be lower, so the reported gap
is conservative.

**Seed sensitivity of quantized metrics.** False-confidence is a fraction over a small set of named
fields and therefore takes quantized values (0, 1/3, 1/2, ...); a small rescaling of attributions can
move it between levels. We report it as a mean with standard deviation over five seeds and give the
per-seed values, and we distinguish claims that hold in every seed (saliency false-confidence,
occlusion's clean record) from those that are seed-contingent (the exact strength at which Integrated
Gradients or DeepSHAP first fabricates importance).
