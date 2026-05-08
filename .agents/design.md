# DermAI Design System

**Theme:** Clean Clinical (Màu trắng & Xanh bác sĩ)
**Mục tiêu:** Tạo cảm giác chuyên nghiệp, sạch sẽ, đáng tin cậy của một ứng dụng y tế, kết hợp với các hiệu ứng hiện đại (Light Glassmorphism, Soft Shadows, Smooth Transitions).

## 1. Color Palette

### 1.1. Core Colors
- **Medical Blue (Primary):** `#0284c7` (Trấn an, chuyên nghiệp)
- **Medical Blue Light:** `#e0f2fe` (Dùng cho background hover, highlight nhẹ)
- **Medical Blue Deep:** `#0369a1` (Dùng cho active states, text nhấn mạnh)
- **White (Background):** `#ffffff`
- **Off-White (App Background):** `#f8fafc` (Màu nền chính của toàn ứng dụng để tạo độ tương phản với các card trắng)

### 1.2. Text Colors
- **Text Primary:** `#0f172a` (Tiêu đề, nội dung chính)
- **Text Secondary:** `#475569` (Phụ đề, mô tả)
- **Text Tertiary:** `#94a3b8` (Placeholder, hint)

### 1.3. Risk Colors (Trạng thái bệnh)
- **Low Risk (Lành tính):** `#10b981` (Emerald Green)
- **Medium Risk (Theo dõi):** `#f59e0b` (Amber)
- **High Risk (Nguy hiểm):** `#ef4444` (Red)
- **Critical Risk (Rất nguy hiểm):** `#b91c1c` (Deep Red)

## 2. Typography
- **Headings & Accents:** `Outfit`, sans-serif (Trọng lượng: 500, 600, 700, 800)
- **Body Text:** `Inter`, sans-serif (Trọng lượng: 400, 500)

## 3. UI Components & Effects

### 3.1. Light Glassmorphism
Sử dụng trên các Navbar và Panel lơ lửng:
```css
background: rgba(255, 255, 255, 0.75);
backdrop-filter: blur(16px);
border: 1px solid rgba(255, 255, 255, 0.5);
box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05);
```

### 3.2. Shadows
Sử dụng đổ bóng mềm để phân tầng thông tin:
```css
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
```

### 3.3. Buttons
- **Primary Action (Nút Phân Tích):** Nền Gradient Xanh Bác Sĩ (vd: `#0ea5e9` to `#0284c7`), chữ trắng, hiệu ứng bóng mờ khi hover và transform translateY.
- **Secondary Action (Nút Chọn Ảnh):** Nền trắng, viền `#0284c7`, chữ `#0284c7`.

## 4. Layout Structure
- **Navbar:** Thanh điều hướng mỏng, sticky ở trên cùng.
- **Hero Section:** Tiêu đề lớn, câu chào mừng rõ ràng với nền trắng tinh khôi và họa tiết y tế chìm hoặc các dạng lượn sóng (waves) nhẹ.
- **Main App Grid:** Hai cột rõ ràng. Cột trái (Tải ảnh lên) - Cột phải (Kết quả).
- **Cards Section:** Khu vực giới thiệu 7 loại bệnh dưới dạng các thẻ (cards) sạch sẽ.
