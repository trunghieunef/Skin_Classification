"""
app.py — Flask Web Application
Chạy: python web/app.py
API:
  POST /api/predict  — upload ảnh, nhận kết quả phân loại
  GET  /api/health   — kiểm tra trạng thái
"""

import os
import io
import sys
import torch
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image

# Thêm root project vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.predict import load_predictor, SkinPredictor

# ─────────────────────────── App Setup ───────────────────────────────

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}

predictor: SkinPredictor = None
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'models', 'best_model.pth'
)


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_model():
    global predictor
    if os.path.exists(MODEL_PATH):
        try:
            predictor = load_predictor(MODEL_PATH, device)
            print(f"[OK] Model loaded successfully from {MODEL_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            predictor = None
    else:
        print(f"[WARN] Model file not found at {MODEL_PATH}")
        print("  Train the model first using the Colab notebook.")
        predictor = None


# ─────────────────────────── Routes ──────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({
        'status':       'ok',
        'model_loaded': predictor is not None,
        'device':       str(device),
        'model_path':   MODEL_PATH,
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    if predictor is None:
        return jsonify({
            'error': 'Model chưa được load. Hãy train model trước và đặt file best_model.pth vào thư mục models/'
        }), 503

    if 'file' not in request.files:
        return jsonify({'error': 'Không có file được gửi lên'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tên file trống'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Định dạng không hỗ trợ. Cho phép: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Kiểm tra kích thước tối thiểu
        if image.width < 50 or image.height < 50:
            return jsonify({'error': 'Ảnh quá nhỏ (tối thiểu 50x50 pixels)'}), 400

        result = predictor.predict(image)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Lỗi xử lý ảnh: {str(e)}'}), 500


# ─────────────────────────── Entry Point ─────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  Skin Disease Classification Web App")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")

    init_model()
    app.run(debug=False, host='0.0.0.0', port=5000)
