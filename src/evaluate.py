"""
evaluate.py — Đánh giá mô hình toàn diện
- Weighted F1, Macro F1, Balanced Accuracy, Macro AUC-ROC
- Confusion Matrix (raw + normalized)
- ROC Curves per class
- Per-class metrics bảng đẹp
"""

import os
import numpy as np
import torch
from torch.cuda.amp import autocast
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, balanced_accuracy_score,
    roc_curve, auc,
)
from sklearn.preprocessing import label_binarize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

from src.dataset import CLASS_NAMES


# ──────────────────────── Prediction Collection ──────────────────────

@torch.no_grad()
def get_predictions(model, loader, device):
    """
    Chạy inference trên toàn bộ loader.
    Returns: (labels, preds, probs) — numpy arrays
    """
    model.eval()
    all_labels, all_preds, all_probs = [], [], []

    for images, labels in tqdm(loader, desc='Evaluating', ncols=90):
        images = images.to(device, non_blocking=True)
        with autocast():
            outputs = model(images)
            probs   = torch.softmax(outputs, dim=1)

        all_preds.extend(probs.argmax(dim=1).cpu().numpy())
        all_probs.extend(probs.cpu().numpy())
        all_labels.extend(labels.numpy())

    return (np.array(all_labels),
            np.array(all_preds),
            np.array(all_probs))


# ──────────────────────── Main Evaluate Function ─────────────────────

def evaluate_model(model, loader, device, output_dir: str = None):
    """
    Đánh giá đầy đủ và in báo cáo. Tùy chọn lưu biểu đồ.

    Returns: dict chứa tất cả metrics
    """
    labels, preds, probs = get_predictions(model, loader, device)

    # ── Scalar metrics ──────────────────────────────────────────────
    weighted_f1   = f1_score(labels, preds, average='weighted', zero_division=0)
    macro_f1      = f1_score(labels, preds, average='macro',    zero_division=0)
    balanced_acc  = balanced_accuracy_score(labels, preds)
    per_class_f1  = f1_score(labels, preds, average=None,       zero_division=0)

    # ── AUC-ROC ─────────────────────────────────────────────────────
    try:
        y_bin      = label_binarize(labels, classes=list(range(len(CLASS_NAMES))))
        auc_scores = roc_auc_score(y_bin, probs, average=None, multi_class='ovr')
        macro_auc  = float(np.mean(auc_scores))
    except Exception as e:
        print(f"  AUC warning: {e}")
        auc_scores = [0.0] * len(CLASS_NAMES)
        macro_auc  = 0.0

    # ── Print Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  MODEL EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Weighted F1      : {weighted_f1:.4f}")
    print(f"  Macro F1         : {macro_f1:.4f}")
    print(f"  Balanced Accuracy: {balanced_acc:.4f}")
    print(f"  Macro AUC-ROC    : {macro_auc:.4f}")
    print("\n  Per-Class Metrics:")
    print(f"  {'Class':>8}  {'F1':>6}  {'AUC':>6}")
    print(f"  {'-'*24}")
    for cls, f1, a in zip(CLASS_NAMES, per_class_f1, auc_scores):
        print(f"  {cls:>8}  {f1:>6.4f}  {a:>6.4f}")
    print()
    print(classification_report(labels, preds, target_names=CLASS_NAMES,
                                zero_division=0))

    results = {
        'weighted_f1':    weighted_f1,
        'macro_f1':       macro_f1,
        'balanced_acc':   balanced_acc,
        'macro_auc':      macro_auc,
        'per_class_f1':   dict(zip(CLASS_NAMES, per_class_f1.tolist())),
        'per_class_auc':  dict(zip(CLASS_NAMES, [float(a) for a in auc_scores])),
        'labels':         labels,
        'preds':          preds,
        'probs':          probs,
    }

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        _plot_confusion_matrix(labels, preds, output_dir)
        _plot_roc_curves(labels, probs, output_dir)
        _plot_per_class_metrics(per_class_f1, auc_scores, output_dir)

    return results


# ──────────────────────── Plot Helpers ───────────────────────────────

def _plot_confusion_matrix(labels, preds, output_dir):
    cm  = confusion_matrix(labels, preds)
    cm_norm = cm.astype('float') / cm.sum(axis=1, keepdims=True)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle('Confusion Matrix', fontsize=16, fontweight='bold')

    kw = dict(xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
    sns.heatmap(cm,      annot=True, fmt='d',    cmap='Blues', ax=axes[0], **kw)
    axes[0].set_title('Raw Counts')
    axes[0].set_xlabel('Predicted'); axes[0].set_ylabel('True')

    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues', ax=axes[1], **kw)
    axes[1].set_title('Normalized')
    axes[1].set_xlabel('Predicted'); axes[1].set_ylabel('True')

    plt.tight_layout()
    path = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Confusion matrix saved → {path}")


def _plot_roc_curves(labels, probs, output_dir):
    y_bin  = label_binarize(labels, classes=list(range(len(CLASS_NAMES))))
    colors = plt.cm.Set1(np.linspace(0, 0.9, len(CLASS_NAMES)))

    fig, ax = plt.subplots(figsize=(10, 8))
    for i, (cls, color) in enumerate(zip(CLASS_NAMES, colors)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], probs[:, i])
        roc_auc     = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=2,
                label=f'{cls}  (AUC = {roc_auc:.3f})')

    ax.plot([0, 1], [0, 1], 'k--', lw=1.5)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves (One-vs-Rest)', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, 'roc_curves.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ROC curves saved → {path}")


def _plot_per_class_metrics(per_class_f1, auc_scores, output_dir):
    x   = np.arange(len(CLASS_NAMES))
    w   = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - w/2, per_class_f1, w, label='F1 Score',  color='#2196F3', alpha=0.85)
    bars2 = ax.bar(x + w/2, auc_scores,   w, label='AUC-ROC',   color='#FF5722', alpha=0.85)

    ax.set_xticks(x); ax.set_xticklabels(CLASS_NAMES, rotation=15)
    ax.set_ylim([0, 1.05])
    ax.set_ylabel('Score'); ax.set_title('Per-Class F1 Score & AUC-ROC',
                                          fontsize=14, fontweight='bold')
    ax.legend(); ax.grid(axis='y', alpha=0.3)

    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.01,
                f'{h:.2f}', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.01,
                f'{h:.2f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    path = os.path.join(output_dir, 'per_class_metrics.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Per-class metrics saved → {path}")
