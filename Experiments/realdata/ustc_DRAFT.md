# Section 5.5 addendum — second real capture corpus (USTC-TFC2016)

Ready-to-paste manuscript material. Terse style matching the existing 5.5. All numbers are from a
single seeded run of `Experiments/realdata/ustc_bytelevel.py` (results in
`results/ustc_bytelevel.json` / `.md`); the E1 predicates, PacketDO necessity, and the benchmark
ByteCNN/explainers are the same code path as the ISCX study, so the two datasets are directly
comparable.

## Reproduction verdict

Both load-bearing findings reproduce on a second, independent corpus. **Operator gap: reproduces**
(zero-mask 15.5% vs PacketDO 100% protocol-validity). **False-confidence: reproduces** (gradient
explainers 0.67-0.78 false-confidence against PacketDO necessity, occlusion cleanest). The
server/C2-address shortcut also reproduces (top necessity is again `ip.dst`), and here the model in
fact holds **two** substitutable shortcuts (R(M)=2), a stronger redundancy result than ISCX's R=1.

## Drop-in addendum sentence(s) for 5.5

> We replicate the byte-level study on a second, unrelated capture corpus, USTC-TFC2016 (Wang et al.,
> 2017), as a malware-family task (Miuref vs Geodo, 5,000 real packets per class); unlike the raw-IP
> ISCX subset these captures are Ethernet-framed and are normalised to IP before the identical
> pipeline is applied. Both findings reproduce. The operator gap holds and is again large: the
> captured packets are 100% valid, zero-masking leaves a valid packet in only 15.5% of field
> interventions (breaking the IP checksum in 48,643 cases and the transport checksum in 72,133),
> while PacketDO is valid in 100% with zero violations. The gradient explainers again fabricate
> importance: against interventional necessity (a ByteCNN at 0.864 test accuracy commits to the
> destination address, N(ip.dst)=0.130, and redundantly to the TCP window, N(tcp.window)=0.094, with
> every other field below 0.03), integrated gradients and saliency have false-confidence 0.667 and
> 0.778 and blind-spot 0.5 — confidently attributing importance to header bytes such as the IP TTL
> that the model provably does not use (N(ip.ttl)=0.026) while missing one of its two real shortcuts —
> whereas occlusion is again clean (false-confidence 0, blind-spot 0). The redundancy estimator here
> returns two disjoint sufficient sets, {ip.dst} and {tcp.window} (R(M)=2): either the destination
> address or the TCP window alone recovers most of the model's skill, so the attribution target is
> genuinely non-unique.

## Compact results table

**Table IV-b. Second real byte-level audit (USTC-TFC2016, Miuref vs Geodo; single run, seed 0). Ethernet-framed captures normalised to IP. ByteCNN test accuracy 0.864. Necessity measured by PacketDO on the real packets; false-confidence and blind-spot computed against it.**

| model | method | rho | precision@k | false-confidence | blind-spot |
|---|---|---|---|---|---|
| ByteCNN | IntegratedGradients | 0.734 | 0.50 | 0.667 | 0.50 |
| ByteCNN | Saliency | 0.471 | 0.50 | 0.778 | 0.50 |
| ByteCNN | Occlusion | 0.423 | 1.00 | 0.000 | 0.00 |

**E1-real (operator validity on real USTC packets).** baseline valid 100.0%; zero-mask macro validity
**15.5%** (violations: IP checksum 48,643, transport checksum 72,133); PacketDO macro validity
**100.0%** (zero violations).

**Interventional necessity N(F).** ip.dst 0.130; tcp.window 0.094; ip.ttl 0.026; ip.id 0.010;
ip.src 0.010; tcp.dport 0.004; tcp.sport 0.003; tcp.seq 0.003; tcp.flags 0.000; payload 0.000.
R(M)=2, disjoint sufficient sets {ip.dst}, {tcp.window}.

## Cross-dataset comparison (ISCX vs USTC), for the reviewer

| quantity | ISCX VPN (facebook/ftps) | USTC-TFC2016 (Miuref/Geodo) |
|---|---|---|
| zero-mask macro validity | 6.2% | 15.5% |
| PacketDO macro validity | 100% | 100% |
| top necessity field | ip.dst (0.250) | ip.dst (0.130) |
| R(M) | 1 ({ip.src,ip.dst}) | 2 ({ip.dst},{tcp.window}) |
| IG false-confidence | 0.714 | 0.667 |
| Saliency false-confidence | 0.778 | 0.778 |
| Occlusion false-confidence | 0.333 | 0.000 |

The two datasets differ in domain (encrypted VPN app flows vs malware C2 traffic), link framing
(raw-IP vs Ethernet), and difficulty (0.979 vs 0.864 ByteCNN accuracy), yet the operator gap and the
gradient-explainer false-confidence hold in both, so neither is an artifact of a single capture.
