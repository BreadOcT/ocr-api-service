# Panduan Deployment OCR API Service

## Persyaratan Sistem

- **OS:** Ubuntu 20.04+ / Debian 11+
- **Python:** 3.9+
- **RAM:** Minimal 2GB (PaddleOCR cukup berat)
- **Disk:** 2GB+ free (untuk model PaddleOCR)
- **Domain:** `ocrservice.kolab.top` (A record mengarah ke IP server)

---

## 1. Clone Repository

```bash
git clone https://github.com/BreadOcT/ocr-api-service.git /opt/ocr-api-service
cd /opt/ocr-api-service
```

---

## 2. Environment & Dependencies

Buat virtual environment dan install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Catatan:** PaddlePaddle dan PaddleOCR membutuhkan library system tambahan. Jalankan:

```bash
sudo apt update
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

---

## 3. Build / Setup

Tidak ada proses build khusus (Python). Pastikan model PaddleOCR terunduh dengan menjalankan sekali:

```bash
source venv/bin/activate
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en')"
```

Perintah ini akan mengunduh model OCR (~300MB) pada eksekusi pertama.

---

## 4. Menjalankan Server (Development)

```bash
source venv/bin/activate
python ocr_server.py
```

Server akan berjalan di `http://0.0.0.0:8000`.

Atau dengan uvicorn langsung (recommended):

```bash
source venv/bin/activate
uvicorn ocr_server:app --host 0.0.0.0 --port 8000
```

---

## 5. Menjalankan Server (Production)

Gunakan `gunicorn` dengan worker `uvicorn`:

```bash
source venv/bin/activate
pip install gunicorn
gunicorn -w 2 -k uvicorn.workers.UvicornWorker ocr_server:app --bind 0.0.0.0:8000
```

---

## 6. Reverse Proxy dengan Nginx + SSL (Let's Encrypt)

### A. Pasang Nginx

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### B. Konfigurasi Nginx

Buat file `/etc/nginx/sites-available/ocr-api`:

```nginx
server {
    listen 80;
    server_name ocrservice.kolab.top;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        client_max_body_size 50m;
    }
}
```

Aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/ocr-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### C. SSL dengan Let's Encrypt

```bash
sudo certbot --nginx -d ocrservice.kolab.top
```

---

## 7. Systemd Service (Agar Auto-restart)

Buat file `/etc/systemd/system/ocr-api.service`:

```ini
[Unit]
Description=OCR API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/ocr-api-service
Environment="PATH=/opt/ocr-api-service/venv/bin"
ExecStart=/opt/ocr-api-service/venv/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker ocr_server:app --bind 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktifkan:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ocr-api
sudo systemctl status ocr-api
```

---

## 8. Firewall

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

---

## 9. Verifikasi

Cek endpoint:

```bash
curl -X POST "https://ocrservice.kolab.top/scan-base64/" \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64_string>"}'
```

---

## Ringkasan Perintah Penting

| Aksi | Perintah |
|------|----------|
| Start service | `sudo systemctl start ocr-api` |
| Stop service | `sudo systemctl stop ocr-api` |
| Restart service | `sudo systemctl restart ocr-api` |
| Lihat log | `sudo journalctl -u ocr-api -f` |
| Update kode | `git pull && sudo systemctl restart ocr-api` |

---

## Environment Variables (Optional)

Jika ingin port bisa dikonfigurasi via environment, tambahkan file `.env`:

```
PORT=8000
HOST=0.0.0.0
```

Saat ini kode menggunakan nilai hardcoded (`host="0.0.0.0", port=8000`). Jika ingin fleksibel, Anda bisa memodifikasi `ocr_server.py` untuk membaca dari environment variable.
