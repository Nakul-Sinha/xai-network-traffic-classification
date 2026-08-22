# 3. Method: protocol-valid intervention and interventional ground truth

## 3.1 The problem with feature deletion on packets

Let a classifier `M` map a packet (or a flow of packets) to a label. Post-hoc faithfulness metrics
estimate the importance of a feature `F` by *removing* it and measuring the change in `M`'s output.
In the byte and flow representations used for traffic, "removing" a feature has no natural meaning,
so the literature borrows the vision convention: set the feature to a baseline, almost always zero.

This is unsound for two reasons specific to network data. First, the fields of a packet are not
independent: an IP or transport checksum is a function of the other header and payload bytes, and the
IP total-length and TCP data-offset fields are functions of the packet's structure. Zeroing any
field that a checksum covers -- which is almost all of them -- leaves the checksum inconsistent, so
the byte string is no longer a packet any host could emit. The model is then evaluated on an input
drawn from a region of byte space with zero probability under any real traffic distribution, and the
"importance" it reports is confounded by that extrapolation. Second, for raw-byte models a fixed byte
offset does not correspond to a fixed semantic field across samples: when one class carries an
Ethernet header and another does not, byte 49 is the IP protocol field in one class and part of an
Ethernet address in the other, so an attribution to a byte index is an attribution to a moving
target. Section 5.1 measures how often the zero-masking operator actually produces an invalid packet.

## 3.2 PacketDO

We replace deletion with a protocol-valid intervention. For a field `F` and a trained, frozen model
`M`, `PacketDO` performs the operation

  do(F := f),  f ~ pooled empirical marginal of F over the whole dataset,

by (i) setting `F` to the resampled value `f` on the packet, (ii) recomputing every field that
structurally depends on `F` -- the IP header checksum, the transport (TCP/UDP) checksum, the IP total
length, the TCP data offset, and the UDP length -- and (iii) re-emitting the packet through the
protocol serializer so that the result is a well-formed packet. The model's own preprocessing is then
re-applied: for a byte model the byte window is re-extracted from the intervened packet, and for a
flow model the flow features are recomputed. The intervention is inference-time only; `M` is never
retrained.

Three properties make this the right null operation. It is **on-manifold**: because the field is set
to a value drawn from real traffic and all dependent fields are recomputed, the counterfactual is a
packet a host could send. It is **information-destroying but distribution-preserving**: sampling `f`
class-agnostically leaves the marginal distribution of `F` unchanged while destroying its mutual
information with the label, which is exactly the semantics of a `do()` intervention rather than a
deletion. And it is **representation-agnostic**: the same packet-level operation drives the ground
truth for a raw-byte CNN and for a flow-feature random forest.

Not every header field is a free degree of freedom. The IP protocol number is fixed by the transport
header that follows it (protocol 6 requires a TCP payload, 17 a UDP payload); resampling it while
leaving the transport bytes in place yields a self-inconsistent packet, exactly as a stale checksum
does. We therefore treat the protocol number, alongside checksums and length fields, as a structural
field that PacketDO recomputes rather than resamples. Identifying the free degrees of freedom of a
packet is itself part of defining what an intervention on traffic means.

## 3.3 Interventional ground truth

With a valid intervention in hand, we define the quantities the rest of the paper treats as ground
truth. All are properties of the trained model `M`, measured by inference on a held-out set, not
assumed from the data:

- **Necessity** `N(F) = Acc(M) - Acc(M under do(F := resample))`: how much accuracy the model loses
  when field `F` is stripped of its label information. A field the model does not use has `N(F) = 0`.
- **Sufficiency** `S(F) = Acc(M under do(every field except F := resample))`: how far `F` alone
  carries the model.
- **Redundancy degree** `R(M)`: the number of disjoint, individually-sufficient field sets. We
  extract a minimal sufficient set by greedy interventional removal, neutralize it, and repeat on the
  remainder until accuracy falls to chance. `R(M) > 1` means the model holds substitutable shortcuts,
  so no single feature set is *the* explanation and any method that returns one is under-determined.

We report a **null-intervention control** with every table: a field that the data never correlates
with the label must yield `N(F) approx 0`, which validates the estimator (resampling an unused field
does not move accuracy) and calibrates the noise floor for the necessity estimates.

## 3.4 Auditing an explainer against the ground truth

An explainer produces per-feature importance in the model's own representation (per-byte for the CNN,
per-feature for the forest). We aggregate byte-level attributions to protocol fields using the
header-offset map, so that every explainer is scored in the same field vocabulary as `N(F)`. For a
model-dataset cell we then report: the Spearman correlation between the attribution ranking and the
`N(F)` ranking; precision at `k` (with `k` the number of fields whose necessity exceeds a threshold);
the **false-confidence rate**, the fraction of fields the explainer confidently attributes importance
to whose necessity is approximately zero; and the **blind-spot rate**, the fraction of
truly-necessary fields the explainer leaves out of its top-`k`. False confidence and blind spots are
the two ways an attribution can disagree with what the model actually uses, and they are the metrics
that carry our results.
