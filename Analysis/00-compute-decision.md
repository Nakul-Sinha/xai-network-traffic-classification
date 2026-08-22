# Compute decision (Phase 0)

| Resource | Status | Use |
|---|---|---|
| Local GPU | **RTX 4050 Laptop (CUDA available, torch 2.6+cu124)** | PRIMARY: all training incl. 1D-CNN and ET-BERT fine-tune |
| GCP billing | account 0138C5-... exists but OPEN=False (closed) | not usable; not needed |
| Kaggle | token in .env works; USTC-TFC2016 + CIC-IDS mirrors reachable | dataset source; fallback GPU notebooks |
| Local disk C: | 18 GB free of 329 GB (95% used) | CONSTRAINT: stage large PCAPs to scratchpad, delete after feature extraction |

Decision: run the entire paper on the local RTX 4050. GCP not required (billing closed; the RTX 4050
exceeds what the experiments need). Kaggle is the dataset mirror and a GPU fallback.
Disk is the binding constraint - byte datasets are ~2 GB each; extract features/byte-windows then
delete raw PCAPs; keep only derived tensors.
