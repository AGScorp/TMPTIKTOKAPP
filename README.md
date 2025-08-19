# holoApp — TikTok Web Application (FastAPI + Frontend)

แอปพลิเคชันเว็บสำหรับเชื่อมต่อ TikTok API v2 เพื่อ
- เข้าสู่ระบบด้วย TikTok OAuth2
- แสดงข้อมูลผู้ใช้ (โปรไฟล์/สถิติพื้นฐาน)
- เรียกดูรายการวิดีโอ และ Query วิดีโอตาม video_ids
- มีหน้า UI (Single Page) พร้อมเชื่อมต่อ API

อ้างอิงแนวคิดจาก SDK PHP ในโฟลเดอร์ `ref/` และพอร์ตส่วนที่จำเป็นมาเป็น Client ฝั่ง Python ด้วย httpx

## สแต็คเทคโนโลยี
- Backend: FastAPI (Python)
- HTTP Client: httpx (async)
- Frontend: HTML/CSS/JS (Vanilla)
- Config: `.env`

## โครงสร้างโปรเจค
- แอปหลัก FastAPI: `app/`
  - ตั้งค่าและคอนฟิก: [app/core/config.py](app/core/config.py)
  - จุดเริ่มต้นแอป: [app/main.py](app/main.py)
  - TikTok Client (Python): [app/services/tiktok_client.py](app/services/tiktok_client.py)
  - เส้นทาง OAuth: [app/routers/auth.py](app/routers/auth.py)
  - เส้นทาง API วิดีโอ/ผู้ใช้: [app/routers/videos.py](app/routers/videos.py)
- หน้าเว็บและไฟล์ Static: `web/`
  - UI หลัก: [web/index.html](web/index.html)
  - สไตล์: [web/styles.css](web/styles.css)
  - สคริปต์ฝั่งหน้าเว็บ: [web/app.js](web/app.js)
- อ้างอิง PHP SDK: `ref/` (ไม่จำเป็นต้องรันตรงๆ ใช้เพื่อดูโครงสร้าง/พารามิเตอร์)

## การตั้งค่า Environment (.env)
ตัวอย่างคีย์ที่ใช้ (โปรเจคนี้มีให้แล้ว):
```
HOST=0.0.0.0
PORT=8100

TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_REDIRECT_URI=https://.../auth/callback   # ค่าใน .env ปัจจุบันชี้ไปที่โดเมนภายนอก
TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats,video.upload,video.publish
TIKTOK_BASE_URL=https://open.tiktokapis.com/v2
```

หมายเหตุ:
- ในสภาพแวดล้อมพัฒนา (local) แนะนำให้ตั้ง `TIKTOK_REDIRECT_URI=http://localhost:8100/auth/callback` และต้องลงทะเบียนค่า Redirect URI เดียวกันใน TikTok Developer Console
- โปรดรักษาความลับของ `TIKTOK_CLIENT_SECRET`

## การติดตั้งและรัน (Development)
ต้องมี Python 3.10+ หรือ 3.11+

1) สร้าง virtualenv และติดตั้ง dependencies
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) รันเซิร์ฟเวอร์ FastAPI (Uvicorn)
```
uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8100} --reload
```

3) เปิดเบราว์เซอร์ไปที่
```
http://localhost:8100/
```
- ปุ่ม “เข้าสู่ระบบด้วย TikTok” จะพาไปยังหน้าอนุญาตสิทธิ์ของ TikTok
- เมื่ออนุญาตสำเร็จ ระบบจะ Redirect กลับมาที่ `/auth/callback` และบันทึก cookie token

4) เอกสาร API แบบ interactive
```
http://localhost:8100/docs
```

## รายละเอียดเส้นทาง (Routes)
Backend:
- GET `/healthz` — ตรวจสุขภาพระบบ
- GET `/` — ส่งหน้า [web/index.html](web/index.html)
- GET `/auth/login` — เริ่ม OAuth (redirect ไป TikTok)
- GET `/auth/callback` — จุดรับ callback จาก TikTok (บันทึก cookie: access_token/refresh_token/open_id)
- POST `/auth/logout` — ล้าง cookie และออกจากระบบ
- GET `/api/me` — ดึงข้อมูลผู้ใช้ปัจจุบันจาก TikTok (ต้องมี cookie access token)
- POST `/api/videos` — ดึงรายการวิดีโอ (body: `{ "max_count": 20, "cursor": "..." }`)
- POST `/api/videos/query` — ตรวจสอบวิดีโอตาม `video_ids` (body: `{ "video_ids": ["..."] }`)

Frontend:
- หน้าเดียว (Single Page) ที่ [web/index.html](web/index.html) เรียก API ผ่าน fetch และแสดงผล

## การแมปอ้างอิงจาก PHP SDK → Python Client
- ผู้ใช้:
  - PHP: [ref/User/User.php](ref/User/User.php) → Python: [app/services/tiktok_client.py](app/services/tiktok_client.py) เมธอด `get_user_info`
- วิดีโอ:
  - PHP: [ref/Video/Video.php](ref/Video/Video.php) → Python: [app/services/tiktok_client.py](app/services/tiktok_client.py) เมธอด `list_videos`, `query_videos`
- การขอ Token:
  - ฐาน URL ตาม `.env` → ใช้ `POST /oauth/token/` กับฟอร์ม `application/x-www-form-urlencoded`

## ประเด็นด้านความปลอดภัย/โปรดักชัน
- Cookie ใน [app/routers/auth.py](app/routers/auth.py) ตั้ง `secure=False` เพื่อให้ง่ายต่อการทดสอบบน HTTP ในเครื่อง หากขึ้นโปรดักชันควร:
  - เปิดใช้งาน HTTPS แล้วตั้ง `secure=True`
  - ตั้งค่า CORS เฉพาะโดเมนที่ต้องการ
  - ทบทวนอายุ cookie และนโยบาย `SameSite`
- ตรวจสอบให้แน่ใจว่า Redirect URI ใน `.env` ตรงกับที่ลงทะเบียนใน TikTok Developer Console

## ขั้นต่อไปที่แนะนำ
- เพิ่มการจัดเก็บ token ฝั่ง server (database/redis) หากต้องการ multi-user หรือ session คงทน
- เพิ่มฟีเจอร์อัปโหลดและเผยแพร่วิดีโอ (มี scope ใน `.env` แล้ว)
- เขียนเทสพื้นฐานสำหรับ API