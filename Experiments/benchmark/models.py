"""
Model zoo for the synthetic benchmark: two families whose input representations differ,
so the paper's "attribution granularity depends on representation" point is exercised.

  ByteCNN  : 1D-CNN over the raw packet-byte window (byte-level attribution).
  RFFlow   : RandomForest over named per-packet features (field-level attribution),
             the synthetic analogue of a CICFlowMeter feature vector.

Feature extraction for RFFlow reads the SAME packets, so interventions defined at the
packet layer (PacketDO) map onto both representations consistently.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import torch, torch.nn as nn
from scapy.all import IP, TCP, Raw

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Named features for the RF (field-level). Order fixed -> attribution index maps to field.
RF_FEATURES = ["ip.ttl", "ip.id", "ip.src_b3", "ip.dst_b3", "tcp.sport", "tcp.dport",
               "tcp.window", "tcp.seq_hi", "tcp.flags", "payload_len"]


def packet_to_features(pkt):
    ip = pkt[IP]
    tcp = pkt[TCP] if TCP in pkt else None
    pl = len(bytes(pkt[Raw].load)) if Raw in pkt else 0
    src_b3 = int(ip.src.split(".")[3])
    dst_b3 = int(ip.dst.split(".")[3])
    return np.array([
        ip.ttl, ip.id, src_b3, dst_b3,
        tcp.sport if tcp else 0, tcp.dport if tcp else 0,
        tcp.window if tcp else 0, (tcp.seq >> 24) if tcp else 0,
        int(tcp.flags) if tcp else 0, pl,
    ], dtype=np.float32)


class ByteCNN(nn.Module):
    def __init__(self, win):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(), nn.AdaptiveMaxPool1d(8),
            nn.Flatten(), nn.Linear(64 * 8, 64), nn.ReLU(), nn.Linear(64, 2))

    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (B, 1, WIN)
        return self.net(x)


def train_cnn(X, y, epochs=40, seed=0):
    torch.manual_seed(seed)
    m = ByteCNN(X.shape[1]).to(DEVICE)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    lf = nn.CrossEntropyLoss()
    Xt = torch.tensor(X, dtype=torch.float32).to(DEVICE)
    yt = torch.tensor(y, dtype=torch.long).to(DEVICE)
    m.train()
    for _ in range(epochs):
        opt.zero_grad(); loss = lf(m(Xt), yt); loss.backward(); opt.step()
    m.eval()
    return m


def cnn_acc(m, X, y):
    with torch.no_grad():
        Xt = torch.tensor(X, dtype=torch.float32).to(DEVICE)
        pred = m(Xt).argmax(1).cpu().numpy()
    return float((pred == y).mean())


def cnn_predict(m, X):
    with torch.no_grad():
        Xt = torch.tensor(X, dtype=torch.float32).to(DEVICE)
        return m(Xt).argmax(1).cpu().numpy()


def train_rf(F, y, seed=0):
    from sklearn.ensemble import RandomForestClassifier
    m = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=seed, n_jobs=-1)
    m.fit(F, y)
    return m


def rf_acc(m, F, y):
    return float((m.predict(F) == y).mean())
