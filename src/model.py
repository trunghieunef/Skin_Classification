"""
model.py — EfficientNet-B3 Classifier cho HAM10000
- Transfer learning từ ImageNet pretrained weights (via timm)
- Custom classification head với BatchNorm & Dropout
- Label Smoothing Loss để tránh overconfidence
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

NUM_CLASSES = 7   # akiec, bcc, bkl, df, mel, nv, vasc


# ──────────────────────── Main Model ─────────────────────────────────

class SkinClassifier(nn.Module):
    """
    EfficientNet-B3 backbone + custom classification head.
    Backbone pretrained trên ImageNet, fine-tune toàn bộ.
    """

    def __init__(self,
                 model_name: str = 'efficientnet_b3',
                 num_classes: int = NUM_CLASSES,
                 pretrained: bool = True,
                 dropout: float = 0.4):
        super().__init__()

        # Backbone — loại bỏ classifier gốc, chỉ giữ feature extractor
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,       # trả về features thay vì logits
            global_pool='avg',
        )
        in_features = self.backbone.num_features  # 1536 cho EfficientNet-B3

        # Custom head
        self.classifier = nn.Sequential(
            nn.BatchNorm1d(in_features),
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),                  # Swish activation
            nn.Dropout(p=dropout / 2),
            nn.Linear(512, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        return self.classifier(features)

    def get_backbone_features(self, x: torch.Tensor) -> torch.Tensor:
        """Trả về feature vector trước classifier (dùng cho Grad-CAM)."""
        return self.backbone(x)


# ──────────────────────── Loss Function ──────────────────────────────

class LabelSmoothingLoss(nn.Module):
    """
    Cross-entropy với label smoothing.
    Giúp model không quá tự tin với 1 class → tránh overfit.
    """

    def __init__(self, num_classes: int = NUM_CLASSES,
                 smoothing: float = 0.1,
                 class_weights: torch.Tensor = None):
        super().__init__()
        self.num_classes    = num_classes
        self.smoothing      = smoothing
        self.confidence     = 1.0 - smoothing
        self.class_weights  = class_weights  # (num_classes,) optional

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        log_prob   = F.log_softmax(pred, dim=-1)            # (B, C)
        nll_loss   = -log_prob.gather(dim=-1, index=target.unsqueeze(1)).squeeze(1)  # (B,)
        smooth_loss = -log_prob.mean(dim=-1)                 # (B,)
        loss = self.confidence * nll_loss + self.smoothing * smooth_loss  # (B,)

        if self.class_weights is not None:
            w    = self.class_weights[target]
            loss = loss * w

        return loss.mean()


# ──────────────────────── Factory Function ───────────────────────────

def create_model(model_name: str = 'efficientnet_b3',
                 pretrained: bool = True,
                 class_weights: torch.Tensor = None,
                 device: str = 'cpu'):
    """
    Tạo model + loss function đã được đưa lên device.

    Returns:
        model     (SkinClassifier)
        criterion (LabelSmoothingLoss | CrossEntropyLoss)
    """
    model = SkinClassifier(
        model_name=model_name,
        num_classes=NUM_CLASSES,
        pretrained=pretrained,
    ).to(device)

    if class_weights is not None:
        class_weights = class_weights.to(device)

    criterion = LabelSmoothingLoss(
        num_classes=NUM_CLASSES,
        smoothing=0.1,
        class_weights=class_weights,
    )

    total_params     = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model: {model_name}")
    print(f"Total params:     {total_params:,}")
    print(f"Trainable params: {trainable_params:,}")

    return model, criterion
