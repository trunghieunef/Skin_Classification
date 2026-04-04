"""
dataset.py — HAM10000 Data Pipeline
- Patient-level train/val/test split (tránh data leakage)
- WeightedRandomSampler để xử lý class imbalance
- Strong augmentation với albumentations
"""

import os
import pandas as pd
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
import albumentations as A
from albumentations.pytorch import ToTensorV2

# ──────────────────────────── Constants ─────────────────────────────

CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

CLASS_DESCRIPTIONS = {
    'akiec': 'Actinic Keratoses & Intraepithelial Carcinoma',
    'bcc':   'Basal Cell Carcinoma',
    'bkl':   'Benign Keratosis-like Lesions',
    'df':    'Dermatofibroma',
    'mel':   'Melanoma',
    'nv':    'Melanocytic Nevi',
    'vasc':  'Vascular Lesions',
}

LABEL_MAP     = {name: idx for idx, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS  = {idx: name for name, idx in LABEL_MAP.items()}

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# ──────────────────────────── Helpers ────────────────────────────────

def get_image_path(image_id: str, data_dir: str) -> str:
    """Tìm đường dẫn ảnh trong cả 2 part của HAM10000."""
    for part in ['HAM10000_images_part_1', 'HAM10000_images_part_2']:
        path = os.path.join(data_dir, part, f"{image_id}.jpg")
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Image '{image_id}' not found in {data_dir}")


def patient_level_split(df: pd.DataFrame,
                         val_size: float = 0.15,
                         test_size: float = 0.15,
                         random_state: int = 42):
    """
    Split theo lesion_id để tránh data leakage
    (ảnh của cùng 1 bệnh không xuất hiện ở cả train lẫn val/test).
    """
    unique_patients = df['lesion_id'].unique()

    # Bước 1: tách test patients
    train_val_pts, test_pts = train_test_split(
        unique_patients, test_size=test_size, random_state=random_state
    )

    # Bước 2: tách val từ phần còn lại
    val_ratio = val_size / (1 - test_size)
    train_pts, val_pts = train_test_split(
        train_val_pts, test_size=val_ratio, random_state=random_state
    )

    train_df = df[df['lesion_id'].isin(train_pts)].reset_index(drop=True)
    val_df   = df[df['lesion_id'].isin(val_pts)].reset_index(drop=True)
    test_df  = df[df['lesion_id'].isin(test_pts)].reset_index(drop=True)

    return train_df, val_df, test_df


# ──────────────────────── Augmentation Pipelines ─────────────────────

def get_transforms(phase: str = 'train', image_size: int = 224) -> A.Compose:
    if phase == 'train':
        return A.Compose([
            A.Resize(image_size, image_size),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15,
                               rotate_limit=30, border_mode=0, p=0.6),
            A.OneOf([
                A.ColorJitter(brightness=0.2, contrast=0.2,
                              saturation=0.2, hue=0.1, p=1.0),
                A.HueSaturationValue(hue_shift_limit=15,
                                     sat_shift_limit=35,
                                     val_shift_limit=25, p=1.0),
            ], p=0.6),
            A.OneOf([
                A.GaussNoise(p=1.0),
                A.ISONoise(p=1.0),
            ], p=0.3),
            A.OneOf([
                A.MotionBlur(blur_limit=5, p=1.0),
                A.GaussianBlur(blur_limit=5, p=1.0),
            ], p=0.2),
            A.CoarseDropout(max_holes=8, max_height=image_size // 8,
                            max_width=image_size // 8, p=0.3),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ])
    else:  # val / test
        return A.Compose([
            A.Resize(image_size, image_size),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ])


# ─────────────────────────── Dataset Class ───────────────────────────

class SkinDataset(Dataset):
    """PyTorch Dataset cho HAM10000."""

    def __init__(self, df: pd.DataFrame, data_dir: str,
                 transform: A.Compose = None):
        self.df        = df.reset_index(drop=True)
        self.data_dir  = data_dir
        self.transform = transform
        self.labels    = df['dx'].map(LABEL_MAP).values.astype(np.int64)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row       = self.df.iloc[idx]
        img_path  = get_image_path(row['image_id'], self.data_dir)
        image     = np.array(Image.open(img_path).convert('RGB'))
        label     = int(self.labels[idx])

        if self.transform:
            image = self.transform(image=image)['image']

        return image, label


# ────────────────────────── Sampler Factory ──────────────────────────

def get_weighted_sampler(dataset: SkinDataset) -> WeightedRandomSampler:
    """Tạo sampler để cân bằng class trong mỗi batch training."""
    class_counts   = np.bincount(dataset.labels, minlength=len(CLASS_NAMES))
    class_weights  = 1.0 / np.maximum(class_counts, 1)
    sample_weights = class_weights[dataset.labels]
    return WeightedRandomSampler(
        weights=torch.DoubleTensor(sample_weights),
        num_samples=len(sample_weights),
        replacement=True,
    )


# ──────────────────────── DataLoader Factory ─────────────────────────

def create_dataloaders(data_dir: str,
                       batch_size: int = 32,
                       image_size: int = 224,
                       num_workers: int = 2,
                       val_size: float = 0.15,
                       test_size: float = 0.15):
    """
    Trả về (train_loader, val_loader, test_loader, train_df, val_df, test_df).
    """
    metadata_path = os.path.join(data_dir, 'HAM10000_metadata.csv')
    df = pd.read_csv(metadata_path)
    df['label'] = df['dx'].map(LABEL_MAP)

    train_df, val_df, test_df = patient_level_split(df, val_size, test_size)

    print(f"Split sizes  →  Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
    print(f"Train class distribution:\n{train_df['dx'].value_counts().to_string()}\n")

    train_ds = SkinDataset(train_df, data_dir, get_transforms('train', image_size))
    val_ds   = SkinDataset(val_df,   data_dir, get_transforms('val',   image_size))
    test_ds  = SkinDataset(test_df,  data_dir, get_transforms('test',  image_size))

    sampler       = get_weighted_sampler(train_ds)
    loader_kwargs = dict(num_workers=num_workers, pin_memory=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size,
                              sampler=sampler, **loader_kwargs)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size,
                              shuffle=False, **loader_kwargs)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size,
                              shuffle=False, **loader_kwargs)

    return train_loader, val_loader, test_loader, train_df, val_df, test_df


def get_class_weights(df: pd.DataFrame, device) -> torch.Tensor:
    """Tính class weights để dùng trong loss function."""
    counts  = df['dx'].map(LABEL_MAP).value_counts().sort_index().values
    weights = 1.0 / np.maximum(counts, 1)
    weights = weights / weights.sum() * len(CLASS_NAMES)
    return torch.FloatTensor(weights).to(device)
