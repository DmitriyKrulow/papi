# 🚀 QUICK START GUIDE - PAPI Authentication System

## 📋 5-MINUTE SETUP

### Step 1: Install Dependencies (2 min)
```bash
cd F:\Code\papi\backend
pip install -r requirements.txt
mkdir -p backend\data
```

### Step 2: Run Backend (30 sec)
```bash
python -m src.infrastructure.main
```
✅ Backend running on http://localhost:8888

### Step 3: Run Frontend (30 sec)
Open new console:
```bash
cd F:\Code\papi\frontend
npm install
npm run dev
```
✅ Frontend running on http://localhost:5173

### Step 4: Login (30 sec)
1. Open http://localhost:5173/login
2. Use: **admin** / **admin123**
3. Click "Войти"

### Step 5: Verify (30 sec)
✅ Can access http://localhost:5173/admin
✅ Users.json created in backend/data/
✅ All endpoints working

---

## 🎯 WHAT'S FIXED

| Problem | Status |
|---------|--------|
| Registration not saving | ✅ Fixed |
| 401 Unauthorized | ✅ Fixed |
| Missing profile endpoint | ✅ Added |
| Missing change-password | ✅ Added |
| No initial admin | ✅ Auto-created |
| No admin panel | ✅ Complete |

---

## 📊 DEFAULT CREDENTIALS

```
Username: admin
Password: admin123
```

⚠️ Change immediately after first login!

---

## 🔧 COMMANDS

### Start Backend:
```bash
cd backend
python -m src.infrastructure.main
```

### Start Frontend:
```bash
cd frontend
npm run dev
```

### Reinstall Dependencies:
```bash
cd backend
pip install -r requirements.txt --upgrade
```

---

## 📱 API ENDPOINTS

### Auth:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- PUT /api/auth/profile
- POST /api/auth/change-password

### Admin (admin only):
- GET /api/admin/users
- DELETE /api/admin/users/{id}
- PUT /api/admin/users/{id}/role

---

## 🐛 TROUBLESHOOTING

### Backend not starting:
```bash
pip install -r requirements.txt
```

### 401 error:
- Check port 8888
- Use admin/admin123
- Restart backend

### No admin panel:
- Login as admin
- Check role in users.json

---

## 📂 KEY FILES

**Backend:**
- `backend/src/presentation/http/routers/auth.py`
- `backend/src/infrastructure/db/repositories/user_repository.py`
- `backend/data/users.json` (auto-created)

**Frontend:**
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/pages/AdminPanel.tsx`

**Docs:**
- `AUTH_SYSTEM_COMPLETE.md`
- `ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.md`

---

## ✅ VERIFICATION CHECKLIST

After setup, verify:
- [ ] Backend on http://localhost:8888
- [ ] Frontend on http://localhost:5173
- [ ] Login works with admin/admin123
- [ ] Admin panel accessible
- [ ] Users.json exists
- [ ] Passwords are hashed

---

**Ready to go! 🎉**

For detailed instructions, see `ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.md`
