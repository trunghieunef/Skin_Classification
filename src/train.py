"""
train.py — Training Loop cho HAM10000 Skin Classifier
- Mixed Precision (FP16) training với torch.cuda.amp
- AdamW optimizer với differential learning rates (backbone vs head)
- Warmup + Cosine Annealing scheduler
- Early stopping & best model checkpoint
- Training history & loss curves
"""

import os
import time
import torch
import torch.nn as nn
import numpy as np
from torch.cuda.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from sklearn.metrics import f1_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm


# ────────────────────────────── Trainer ──────────────────────────────

class Trainer:
    """Quản lý toàn bộ quá trình training và validation."""

    def __init__(self, model, criterion, optimizer, scheduler,
                 device, output_dir: str = 'models'):
        self.model      = model
        self.criterion  = criterion
        self.optimizer  = optimizer
        self.scheduler  = scheduler
        self.device     = device
        self.output_dir = output_dir
        self.scaler     = GradScaler()

        os.makedirs(output_dir, exist_ok=True)

        self.history = {
            'train_loss': [], 'val_loss': [],
            'train_acc':  [], 'val_acc':  [],
            'train_f1':   [], 'val_f1':   [],
            'lr': [],
        }
        self.best_val_f1       = 0.0
        self.patience_counter  = 0

    # ─────────────────────── epoch helpers ───────────────────────────

    def _train_epoch(self, loader):
        self.model.train()
        running_loss  = 0.0
        all_preds, all_labels = [], []

        pbar = tqdm(loader, desc='  Train', leave=False, ncols=90)
        for images, labels in pbar:
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)

            with autocast():
                outputs = self.model(images)
                loss    = self.criterion(outputs, labels)

            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.scaler.step(self.optimizer)
            self.scaler.update()

            running_loss += loss.item()
            preds = outputs.detach().argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            pbar.set_postfix(loss=f'{loss.item():.4f}')

        avg_loss = running_loss / len(loader)
        acc = float(np.mean(np.array(all_preds) == np.array(all_labels)))
        f1  = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
        return avg_loss, acc, f1

    @torch.no_grad()
    def _val_epoch(self, loader):
        self.model.eval()
        running_loss = 0.0
        all_preds, all_labels = [], []

        for images, labels in tqdm(loader, desc='    Val', leave=False, ncols=90):
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            with autocast():
                outputs = self.model(images)
                loss    = self.criterion(outputs, labels)

            running_loss += loss.item()
            preds = outputs.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

        avg_loss = running_loss / len(loader)
        acc = float(np.mean(np.array(all_preds) == np.array(all_labels)))
        f1  = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
        return avg_loss, acc, f1

    # ───────────────────────── main train loop ────────────────────────

    def train(self, train_loader, val_loader,
              epochs: int = 50,
              patience: int = 10,
              save_name: str = 'best_model.pth'):

        print(f"\n{'='*60}")
        print(f"  Training on : {self.device}")
        print(f"  Epochs      : {epochs}  |  Patience: {patience}")
        print(f"{'='*60}\n")

        for epoch in range(epochs):
            t0 = time.time()

            tr_loss, tr_acc, tr_f1 = self._train_epoch(train_loader)
            vl_loss, vl_acc, vl_f1 = self._val_epoch(val_loader)

            self.scheduler.step()
            lr = self.optimizer.param_groups[-1]['lr']

            # Record
            self.history['train_loss'].append(tr_loss)
            self.history['val_loss'].append(vl_loss)
            self.history['train_acc'].append(tr_acc)
            self.history['val_acc'].append(vl_acc)
            self.history['train_f1'].append(tr_f1)
            self.history['val_f1'].append(vl_f1)
            self.history['lr'].append(lr)

            elapsed = time.time() - t0
            print(
                f"Epoch [{epoch+1:>3}/{epochs}] "
                f"| TrLoss {tr_loss:.4f}  TrF1 {tr_f1:.4f} "
                f"| VlLoss {vl_loss:.4f}  VlF1 {vl_f1:.4f} "
                f"| LR {lr:.2e} | {elapsed:.0f}s"
            )

            # Checkpoint
            if vl_f1 > self.best_val_f1:
                self.best_val_f1    = vl_f1
                self.patience_counter = 0
                save_path = os.path.join(self.output_dir, save_name)
                torch.save({
                    'epoch':              epoch + 1,
                    'model_state_dict':   self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_f1':             vl_f1,
                    'val_acc':            vl_acc,
                    'history':            self.history,
                }, save_path)
                print(f"  ✓ Best model saved  (Val F1: {vl_f1:.4f})")
            else:
                self.patience_counter += 1
                if self.patience_counter >= patience:
                    print(f"\n  ⚡ Early stopping at epoch {epoch+1}")
                    break

        print(f"\n{'='*60}")
        print(f"  Training complete!  Best Val F1: {self.best_val_f1:.4f}")
        print(f"{'='*60}\n")
        return self.history

    # ───────────────────────── plotting ──────────────────────────────

    def plot_history(self, save_path: str = None):
        epochs = range(1, len(self.history['train_loss']) + 1)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Training History', fontsize=16, fontweight='bold')

        # Loss
        axes[0].plot(epochs, self.history['train_loss'], label='Train', color='#2196F3', lw=2)
        axes[0].plot(epochs, self.history['val_loss'],   label='Val',   color='#FF5722', lw=2)
        axes[0].set_title('Loss'); axes[0].set_xlabel('Epoch')
        axes[0].legend(); axes[0].grid(True, alpha=0.3)

        # F1
        axes[1].plot(epochs, self.history['train_f1'], label='Train', color='#2196F3', lw=2)
        axes[1].plot(epochs, self.history['val_f1'],   label='Val',   color='#FF5722', lw=2)
        axes[1].axhline(y=self.best_val_f1, color='green', ls='--', alpha=0.7,
                        label=f'Best {self.best_val_f1:.3f}')
        axes[1].set_title('Weighted F1'); axes[1].set_xlabel('Epoch')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        # LR
        axes[2].plot(epochs, self.history['lr'], color='#9C27B0', lw=2)
        axes[2].set_title('Learning Rate'); axes[2].set_xlabel('Epoch')
        axes[2].set_yscale('log'); axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Training curve saved → {save_path}")
        plt.show()
        plt.close()


# ─────────────────────── Optimizer Factory ───────────────────────────

def create_optimizer_and_scheduler(model, epochs: int,
                                   lr: float = 1e-3,
                                   warmup_epochs: int = 5):
    """
    AdamW với 2 param groups:
      - backbone: lr * 0.1  (pretrained, cần lr thấp hơn)
      - classifier: lr       (randomly initialized)
    Sau warmup dùng CosineAnnealing.
    """
    backbone_params   = list(model.backbone.parameters())
    classifier_params = list(model.classifier.parameters())

    optimizer = torch.optim.AdamW([
        {'params': backbone_params,   'lr': lr * 0.1},
        {'params': classifier_params, 'lr': lr},
    ], weight_decay=1e-4)

    warmup   = LinearLR(optimizer, start_factor=0.1, end_factor=1.0,
                        total_iters=warmup_epochs)
    cosine   = CosineAnnealingLR(optimizer,
                                 T_max=max(epochs - warmup_epochs, 1),
                                 eta_min=1e-7)
    scheduler = SequentialLR(optimizer, schedulers=[warmup, cosine],
                             milestones=[warmup_epochs])

    return optimizer, scheduler
