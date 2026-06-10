"""Shared torch model definition (used by both trainer and inference)."""

import torch.nn as nn


class RelevanceNet(nn.Module):
    def __init__(self, n_in, hidden_dim=0, dropout=0.0):
        super().__init__()
        if hidden_dim and hidden_dim > 0:
            self.net = nn.Sequential(
                nn.Linear(n_in, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, 1),
            )
        else:
            self.net = nn.Linear(n_in, 1)

    def forward(self, x):
        return self.net(x).squeeze(-1)
