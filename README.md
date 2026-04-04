# Skin Disease Classification — HAM10000

**EfficientNet-B3 | PyTorch | Flask Web App**

Hệ thống phân loại 7 loại tổn thương da từ ảnh dermoscopy, sử dụng bộ dữ liệu HAM10000.

---

## 📁 Cấu Trúc Dự Án

```
Skin_Classification/
├── data/
│   ├── HAM10000_images_part_1/   ← Ảnh dermoscopy (phần 1)
│   ├── HAM10000_images_part_2/   ← Ảnh dermoscopy (phần 2)
│   └── HAM10000_metadata.csv     ← Nhãn & metadata bệnh nhân
├── notebooks/
│   ├── 01_EDA.ipynb              ← Exploratory Data Analysis
│   └── 02_Training_Colab.ipynb  ← Training trên Google Colab
├── src/
│   ├── dataset.py                ← Dataset loader & augmentation
│   ├── model.py                  ← EfficientNet-B3 architecture
│   ├── train.py                  ← Training loop
│   ├── evaluate.py               ← Metrics & visualization
│   └── predict.py                ← Inference pipeline
├── models/
│   └── best_model.pth            ← Weights sau khi training (tự tạo)
├── web/
│   ├── app.py                    ← Flask backend API
│   ├── templates/index.html      ← Web UI
│   └── static/
│       ├── css/style.css         ← Styling
│       └── js/main.js            ← Frontend logic
└── requirements.txt
```

---

## 🦠 7 Loại Bệnh Được Phân Loại

| Code | Tên tiếng Anh | Mức độ nguy hiểm |
|------|--------------|-----------------|
| `akiec` | Actinic Keratoses | 🟡 Cần theo dõi |
| `bcc` | Basal Cell Carcinoma | 🔴 Nguy hiểm |
| `bkl` | Benign Keratosis-like Lesions | 🟢 Lành tính |
| `df` | Dermatofibroma | 🟢 Lành tính |
| `mel` | Melanoma | 🚨 Rất nguy hiểm |
| `nv` | Melanocytic Nevi | 🟢 Lành tính |
| `vasc` | Vascular Lesions | 🟢 Lành tính |

---

## 🚀 Hướng Dẫn Sử Dụng

### Bước 1 — Cài đặt môi trường local

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 2 — Chạy EDA (tùy chọn)

Mở `notebooks/01_EDA.ipynb` với Jupyter để khám phá dữ liệu:

```bash
jupyter notebook notebooks/01_EDA.ipynb
```

### Bước 3 — Training trên Google Colab

1. Upload `notebooks/02_Training_Colab.ipynb` lên [Google Colab](https://colab.research.google.com)
2. **Runtime → Change runtime type → GPU (T4)**
3. Chọn phương thức lấy dataset:
   - **Kaggle API** (khuyến nghị): Upload `kaggle.json`
   - **Thủ công**: Upload dataset lên Google Drive
4. Chạy từng cell theo thứ tự
5. Download `best_model.pth` từ cell cuối

### Bước 4 — Đặt model đã train

```
Skin_Classification/
└── models/
    └── best_model.pth    ← Đặt file vào đây
```

### Bước 5 — Chạy Web App

```bash
python web/app.py
```

Mở browser: **http://localhost:5000**

---

## 🏗️ Kiến Trúc Mô Hình

```
Input (224×224×3)
    ↓
EfficientNet-B3 Backbone (ImageNet pretrained)
    ↓
Global Average Pooling → Feature Vector (1536-dim)
    ↓
BatchNorm → Dropout(0.4) → Linear(512) → BatchNorm → SiLU → Dropout(0.2)
    ↓
Linear(7) → Softmax
    ↓
Output: Probabilities × 7 classes
```

---

## ⚙️ Chi Tiết Training

| Hyperparameter | Giá trị |
|----------------|---------|
| Model | EfficientNet-B3 |
| Image Size | 224 × 224 |
| Batch Size | 32 |
| Optimizer | AdamW (weight_decay=1e-4) |
| Backbone LR | 1e-4 |
| Head LR | 1e-3 |
| Scheduler | Warmup(5ep) + CosineAnnealing |
| Loss Function | Label Smoothing (0.1) + Class Weights |
| Augmentation | Flip, Rotate, ColorJitter, Dropout |
| Class Imbalance | WeightedRandomSampler + Class Weights |
| Mixed Precision | FP16 (torch.cuda.amp) |
| Early Stopping | Patience = 10 |

---

## 📊 Target Metrics

| Metric | Target |
|--------|--------|
| **Weighted F1** | ≥ 0.78 |
| **Macro AUC-ROC** | ≥ 0.85 |
| **Melanoma Recall** | ≥ 0.75 |
| **Balanced Accuracy** | ≥ 0.70 |

---

## 🌐 Web API

### `POST /api/predict`

Upload ảnh và nhận kết quả phân loại.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<image_file>
```

**Response:**
```json
{
  "prediction": "mel",
  "confidence": 0.873,
  "risk_level": "critical",
  "risk_label_vi": "Rất nguy hiểm",
  "description_vi": "Melanoma — ung thư hắc tố...",
  "recommendation": "⚠️ KHẨN CẤP: ...",
  "probabilities": {
    "akiec": 0.012,
    "bcc": 0.045,
    "bkl": 0.031,
    "df": 0.008,
    "mel": 0.873,
    "nv": 0.024,
    "vasc": 0.007
  }
}
```

### `GET /api/health`

Kiểm tra trạng thái server và model.

---

## ⚠️ Disclaimer

**Hệ thống này chỉ dành cho mục đích nghiên cứu và học tập.**  
Kết quả không thay thế cho chẩn đoán của bác sĩ chuyên khoa.  
Luôn tham khảo ý kiến bác sĩ da liễu khi có lo ngại về tình trạng da.

---

## 📚 Dataset

[HAM10000](https://www.kaggle.com/datasets/kmader/skin-lesion-analysis-toward-melanoma-detection) — Human Against Machine with 10000 training images

> Tschandl, P., Rosendahl, C. & Kittler, H. The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions. *Sci Data* 5, 180161 (2018).
