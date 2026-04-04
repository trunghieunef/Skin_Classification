"""
predict.py — Inference Pipeline
- Load trained model từ checkpoint
- Predict single image → trả về dict đầy đủ thông tin
- Dùng trong web app Flask
"""

import torch
import numpy as np
from PIL import Image
from torch.cuda.amp import autocast
import albumentations as A
from albumentations.pytorch import ToTensorV2

from src.dataset import CLASS_NAMES, IMAGENET_MEAN, IMAGENET_STD, CLASS_DESCRIPTIONS
from src.model import SkinClassifier, NUM_CLASSES


# ──────────────────────── Disease Metadata ───────────────────────────

RISK_LEVELS = {
    'akiec': 'medium',
    'bcc':   'high',
    'bkl':   'low',
    'df':    'low',
    'mel':   'critical',
    'nv':    'low',
    'vasc':  'low',
}

RISK_LABELS_VI = {
    'low':      'Lành tính',
    'medium':   'Cần theo dõi',
    'high':     'Nguy hiểm',
    'critical': 'Rất nguy hiểm',
}

RECOMMENDATIONS = {
    'akiec': 'Cần thăm khám bác sĩ da liễu để điều trị sớm. Tổn thương tiền ung thư có thể tiến triển.',
    'bcc':   'Khẩn cấp thăm khám bác sĩ chuyên khoa da liễu. Ung thư tế bào đáy cần điều trị kịp thời.',
    'bkl':   'Tổn thương lành tính. Nên theo dõi định kỳ; gặp bác sĩ nếu có thay đổi kích thước/màu sắc.',
    'df':    'Lành tính, thường không cần điều trị. Theo dõi định kỳ là đủ.',
    'mel':   '⚠️ KHẨN CẤP: Dấu hiệu có thể là Melanoma — ung thư da nguy hiểm nhất. Hãy đến bệnh viện ngay!',
    'nv':    'Nốt ruồi thông thường. Theo dõi nếu thấy thay đổi nhanh về màu, hình dạng, kích thước.',
    'vasc':  'Tổn thương mạch máu. Nên thăm khám bác sĩ để xác định phương án phù hợp.',
}

DESCRIPTIONS_VI = {
    'akiec': 'Dày sừng quang hóa & ung thư biểu mô trong biểu bì — tổn thương tiền ung thư do tia UV.',
    'bcc':   'Ung thư tế bào đáy — dạng ung thư da phổ biến nhất, phát triển chậm.',
    'bkl':   'Dày sừng lành tính — tổn thương da lành tính, rất phổ biến ở người cao tuổi.',
    'df':    'U sợi da — khối u lành tính trong lớp true dermis, thường xuất hiện ở chân.',
    'mel':   'Melanoma — ung thư hắc tố, dạng ung thư da nguy hiểm nhất, cần phát hiện sớm.',
    'nv':    'Nốt ruồi melanocytic — rất phổ biến, thường lành tính nhưng cần theo dõi.',
    'vasc':  'Tổn thương mạch máu — bao gồm u máu, dị dạng mạch máu trên da.',
}


# ────────────────────────── Predictor Class ──────────────────────────

class SkinPredictor:
    """Wrapper inference cho SkinClassifier."""

    def __init__(self, model: SkinClassifier, device, image_size: int = 224):
        self.model      = model.to(device)
        self.model.eval()
        self.device     = device
        self.image_size = image_size

        self._transform = A.Compose([
            A.Resize(image_size, image_size),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ])

    @torch.no_grad()
    def predict(self, image) -> dict:
        """
        Args:
            image: PIL.Image, numpy array (H,W,3), hoặc path str

        Returns:
            dict với prediction, confidence, probabilities, metadata
        """
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        if isinstance(image, Image.Image):
            image = np.array(image.convert('RGB'))

        tensor  = self._transform(image=image)['image'].unsqueeze(0).to(self.device)

        with autocast():
            logits = self.model(tensor)
            probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx   = int(np.argmax(probs))
        pred_class = CLASS_NAMES[pred_idx]
        confidence = float(probs[pred_idx])
        risk       = RISK_LEVELS[pred_class]

        return {
            'prediction':     pred_class,
            'confidence':     round(confidence, 4),
            'risk_level':     risk,
            'risk_label_vi':  RISK_LABELS_VI[risk],
            'description_en': CLASS_DESCRIPTIONS[pred_class],
            'description_vi': DESCRIPTIONS_VI[pred_class],
            'recommendation': RECOMMENDATIONS[pred_class],
            'probabilities':  {
                cls: round(float(p), 4)
                for cls, p in zip(CLASS_NAMES, probs)
            },
        }


# ──────────────────────── Model Loader ───────────────────────────────

def load_predictor(model_path: str, device=None) -> SkinPredictor:
    """
    Load checkpoint và tạo SkinPredictor.

    Args:
        model_path: đường dẫn tới file .pth
        device: torch.device (auto-detect nếu None)
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = SkinClassifier(
        model_name='efficientnet_b3',
        num_classes=NUM_CLASSES,
        pretrained=False,
    )

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])

    val_f1 = checkpoint.get('val_f1', None)
    epoch  = checkpoint.get('epoch', '?')
    print(f"  Model loaded from: {model_path}")
    print(f"  Checkpoint epoch : {epoch}  |  Val F1: {val_f1:.4f}" if val_f1 else "")
    print(f"  Running on       : {device}")

    return SkinPredictor(model, device)
