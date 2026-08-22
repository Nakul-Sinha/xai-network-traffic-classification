# Resource.md - Papers used for this paper

Citations for *Protocol-Valid Faithfulness Evaluation for ML-Based Network Traffic Classifiers*.
Grouped by role in the paper. Full local reading notes: Literature-review/corpus/notes/.

## Core motivation (the problem)

- Jacobs et al., "AI/ML for Network Security: The Emperor has no Clothes" (TRUSTEE), CCS 2022 - the perfect-fidelity-yet-causally-wrong surrogate (Sec. 7.2, Table 3). https://dl.acm.org/doi/10.1145/3548606.3560609 | artifacts: https://github.com/TrusteeML/emperor
- Wickramasinghe et al., "SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers", IEEE S&P 2025 - 348 occlusion experiments, SII/H1/E1-E3 grid, zero XAI terms. https://arxiv.org/abs/2503.20093
- Nascita et al., "A Survey on XAI for Internet Traffic Classification and Prediction, and Intrusion Detection", IEEE COMST 2024 - 5 of 107 papers evaluate explanations; no GT dataset exists. https://ieeexplore.ieee.org/document/10763502
- Warnecke et al., "Evaluating Explanation Methods for Deep Learning in Security", EuroS&P 2020 - descriptive accuracy as admitted indirect proxy. https://arxiv.org/abs/1906.02108
- Arp et al., "Dos and Don'ts of Machine Learning in Computer Security", USENIX Security 2022. https://arxiv.org/abs/2010.09470

## Method ancestors (ground-truth evaluation in other modalities)

- Bastings et al., "Will You Find These Shortcuts?", EMNLP 2022 - shortcut-injection protocol for text; our Track A ancestor. https://arxiv.org/abs/2111.07367
- Yang and Kim, "Benchmarking Attribution Methods with Relative Feature Importance" (BAM), 2019. https://arxiv.org/abs/1907.09701
- Adebayo et al., "Debugging Tests for Model Explanations", NeurIPS 2020. https://arxiv.org/abs/2011.05429
- Zhou et al., "Do Feature Attribution Methods Correctly Attribute Features?", AAAI 2022. https://arxiv.org/abs/2104.14403
- Adebayo et al., "Sanity Checks for Saliency Maps", NeurIPS 2018. https://arxiv.org/abs/1810.03292

## Removal-operator problem (why zero-masking is invalid)

- Hooker et al., "A Benchmark for Interpretability Methods in Deep Neural Networks" (ROAR), NeurIPS 2019. https://arxiv.org/abs/1806.10758
- Rong et al., "A Consistent and Efficient Evaluation Strategy for Attribution Methods" (ROAD), ICML 2022 - zero/fixed-value masking provably worst; imputation image-specific. https://arxiv.org/abs/2202.00449
- Samek et al., "Evaluating the Visualization of What a Deep Neural Network Has Learned", IEEE TNNLS 2017 - AOPC operator dependence. https://arxiv.org/abs/1509.06321
- Petsiuk et al., "RISE: Randomized Input Sampling for Explanation of Black-box Models", BMVC 2018. https://arxiv.org/abs/1806.07421
- DeYoung et al., "ERASER: A Benchmark to Evaluate Rationalized NLP Models", ACL 2020 - comprehensiveness/sufficiency. https://arxiv.org/abs/1911.03429

## Interventions on traffic (direct precedents to cite and differentiate)

- Ponraj, Durairajan, Wang, "Traffic-Explainer", 2025 - checksum-valid byte swapping, confirmatory direction only. https://arxiv.org/abs/2509.18007
- Wang et al., "Bias in the Shadows: Explore Shortcuts in Encrypted Network Traffic Classification" (BiasSeeker), 2026. https://arxiv.org/abs/2601.10180
- Zhao, Boffa, Vassio, Mellia, "ShortcutCatcher: Making Traffic Classification Reliable", Proc. ACM Netw. 2026 - trusts explainers, never validates them. https://doi.org/10.1145/3808671
- "The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification", 2025 - SeqNo/AckNo/timestamp randomization collapses ET-BERT. https://arxiv.org/abs/2507.16438
- Fauvel et al., "LEXNet: A Lightweight, Efficient and Explainable-by-Design CNN for Internet Traffic Classification", 2022 - architectural GT; Grad-CAM 8.2%, SHAP 5.9% prototype recovery. https://arxiv.org/abs/2202.05535

## Dataset artifacts used as natural ground truth (Track B)

- Engelen et al., "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study", SPW 2021 - 25.9% TCP-appendix flows; corrected dataset. https://doi.org/10.1109/SPW53761.2021.00009 | corrected data: https://intrusion-detection.distrinet-research.be/WTMC2021/
- Sharafaldin et al., "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization" (CIC-IDS2017), ICISSP 2018. https://www.unb.ca/cic/datasets/ids-2017.html
- Draper-Gil et al., "Characterization of Encrypted and VPN Traffic Using Time-Related Features" (ISCX VPN-nonVPN), ICISSP 2016. https://www.unb.ca/cic/datasets/vpn.html
- Lanvin et al., "Errors in the CICIDS2017 Dataset and the Significant Differences in Detection Performances It Makes", CRiSIS 2022. https://doi.org/10.1007/978-3-031-31108-6_2

## Audited explainers (method papers)

- Lundberg and Lee, "A Unified Approach to Interpreting Model Predictions" (SHAP), NeurIPS 2017. https://arxiv.org/abs/1705.07874
- Ribeiro et al., "Why Should I Trust You? Explaining the Predictions of Any Classifier" (LIME), KDD 2016. https://arxiv.org/abs/1602.04938
- Sundararajan et al., "Axiomatic Attribution for Deep Networks" (Integrated Gradients), ICML 2017. https://arxiv.org/abs/1703.01365
- Shrikumar et al., "Learning Important Features Through Propagating Activation Differences" (DeepLIFT), ICML 2017. https://arxiv.org/abs/1704.02685
- Zeiler and Fergus, "Visualizing and Understanding Convolutional Networks" (occlusion), ECCV 2014. https://arxiv.org/abs/1311.2901

## Audited models (traffic classifiers)

- Lin et al., "ET-BERT: A Contextualized Datagram Representation with Pre-training Transformers for Encrypted Traffic Classification", WWW 2022. https://arxiv.org/abs/2202.06335 | code: https://github.com/linwhitehat/ET-BERT
- Lotfollahi et al., "Deep Packet: A Novel Approach for Encrypted Traffic Classification Using Deep Learning", 2017. https://arxiv.org/abs/1709.02656
- Wang et al., "End-to-end Encrypted Traffic Classification with One-dimensional Convolution Neural Networks", ISI 2017. https://doi.org/10.1109/ISI.2017.8004872
- Holland et al., "New Directions in Automated Traffic Analysis" (nPrint/nPrintML), CCS 2021. https://arxiv.org/abs/2008.02695

## Supporting results and framing

- Slack et al., "Fooling LIME and SHAP: Adversarial Attacks on Post hoc Explanation Methods", AIES 2020. https://arxiv.org/abs/1911.02508
- Jacovi and Goldberg, "Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?", ACL 2020. https://arxiv.org/abs/2004.03685
- Krishna et al., "The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective", 2022. https://arxiv.org/abs/2202.01602
- Alquliti et al., "Evaluating Explanation Quality in X-IDS Using Feature Alignment Metrics", 2025 - plausibility axis to differentiate from. https://arxiv.org/abs/2505.08006
- Vourganas and Michala, "Stabilising Explainability Fragility in Cybersecurity AI", 2026 - multicollinearity inflates attribution variance. https://arxiv.org/abs/2605.22529
- Wei et al., "xNIDS: Explaining Deep Learning-based Network Intrusion Detection Systems for Active Intrusion Responses", USENIX Security 2023 - downstream consumer of attributions. https://www.usenix.org/conference/usenixsecurity23/presentation/wei-feng
- Geirhos et al., "Shortcut Learning in Deep Neural Networks", Nature MI 2020. https://arxiv.org/abs/2004.07780
- Pendlebury et al., "TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time", USENIX Security 2019. https://arxiv.org/abs/1807.07838

## Reserve (G5 extension: metric meta-evaluation)

- Zaman and Srivastava, "A Causal Lens for Evaluating Faithfulness Metrics", EMNLP 2025 - diagnosticity. https://arxiv.org/abs/2502.18848
- Hedstrom et al., "Quantus: An Explainable AI Toolkit for Responsible Evaluation of Neural Network Explanations", JMLR 2023. https://arxiv.org/abs/2202.06861
- Tomsett et al., "Sanity Checks for Saliency Metrics", AAAI 2020. https://arxiv.org/abs/1912.01451

## Tools

- scapy (packet crafting/rewriting): https://scapy.net
- CICFlowMeter (flow features): https://github.com/ahlashkari/CICFlowMeter
- NFStream (flow features): https://www.nfstream.org
- shap: https://github.com/shap/shap | captum: https://captum.ai | lime: https://github.com/marcotcr/lime

Note. arXiv ids above were carried from the literature phase records; the three entries whose full
text was unavailable during the deep read (see Literature-review/analysis/05, caveats) must be
pulled and verified before final citation in the manuscript.
