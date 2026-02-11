# Quick Start Guide - Sign Language Converter

## ⚡ 3-Step Quick Start

### 1️⃣ Install Dependencies
```bash
cd sign_language_converter
pip install -r requirements.txt
```

### 2️⃣ Run Application
```bash
python app.py
```

### 3️⃣ Open Browser
```
http://localhost:5000
```

---

## 🎮 How to Use

1. **Click "Start Camera"** - Opens webcam feed
2. **Make hand gestures** - System detects 12 signs
3. **Watch recognition** - Signs appear in real-time
4. **Check history** - All predictions stored in database
5. **View statistics** - Dashboard shows trends

---

## 🧠 12 Detectable Gestures

```
1. THUMBS UP ☝️      7. POINTING 👉
2. THUMBS DOWN 👎    8. ROCK SIGN 🤘
3. OK SIGN 👌        9. LOVE YOU ❤️
4. PEACE SIGN ✌️     10. CALL ME ☎️
5. OPEN PALM ✋      11. VICTORY ✌️
6. CLOSED FIST ✊    12. THUMBS SIDEWAYS 👎
```

---

## 📊 Project Structure

```
Backend (Python):
- app.py          → Flask routes
- gesture_model   → Recognition logic
- camera_module   → Webcam streaming
- database        → SQLite storage
- config          → Settings

Frontend (Web):
- index.html      → Main page
- style.css       → Design
- script.js       → Interactivity
```

---

## 🔧 Key Technologies

| Tech | Purpose | Why |
|------|---------|-----|
| Flask | Web backend | Lightweight, beginner-friendly |
| OpenCV | Video capture | Industry standard |
| MediaPipe | Hand detection | Pre-trained, no GPU needed |
| SQLite | Database | No setup required |
| HTML/CSS/JS | Frontend | Standard web tech |

---

## ❓ Common Questions

**Q: Do I need GPU?**  
A: No! Runs perfectly on CPU.

**Q: Can I add new gestures?**  
A: Yes! Edit gesture_model.py and add your logic.

**Q: How do I clear history?**  
A: Click "Clear History" button in the app.

**Q: Can it detect multiple hands?**  
A: Yes, but detects one gesture at a time.

**Q: What if camera doesn't work?**  
A: Check permissions, restart browser, try another USB port.

---

## 🎓 For Your Viva

**Key Points to Remember:**

1. **Architecture**: Frontend (web) ↔ Backend (Flask) ↔ Database (SQLite)
2. **Recognition**: MediaPipe detects hands → We analyze fingers → Pattern matching
3. **Why Flask**: Lightweight, perfect for college projects
4. **Why SQLite**: No server needed, single file database
5. **How Frontend Talks to Backend**: JavaScript fetch() → Flask endpoints → JSON response

---

## 📁 Important Files

| File | Edit for |
|------|----------|
| config.py | Change settings/add gestures |
| gesture_model.py | Modify recognition logic |
| static/css/style.css | Change UI design |
| templates/index.html | Change webpage layout |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera won't start | Restart browser, check permissions |
| Port 5000 in use | Change port in app.py |
| Gestures not detecting | Check lighting, show clearly |
| Slow performance | Close other apps, check CPU |

---

## 💾 Database Info

```
File: sign_language_database.db
Format: SQLite
Table: predictions (id, gesture, timestamp, confidence)
Location: Project root folder
```

---

## 🚀 Deploy to Cloud (Later)

```
Heroku:  heroku create && git push heroku main
AWS:     Use Elastic Beanstalk or EC2
Replit:  Upload to Replit for free hosting
```

---

## 📞 File Structure Reference

```
app.py
├── @app.route('/') - Home page
├── @app.route('/start_camera') - Start camera
├── @app.route('/stop_camera') - Stop camera
├── @app.route('/video_feed') - Stream video
├── @app.route('/api/detect_gesture') - Detect gesture
├── @app.route('/api/predictions') - Get history
├── @app.route('/api/statistics') - Get stats
└── @app.route('/api/clear_data') - Clear database
```

---

## 🎁 Bonus Tips

1. **For Better Detection**: Good lighting is KEY
2. **Add More Gestures**: Easy - just 1 if-statement per gesture
3. **Improve Accuracy**: Adjust confidence thresholds in config.py
4. **Add Logging**: Check Flask terminal for debug info
5. **Test Performance**: Open DevTools (F12) → Performance tab

---

## ✅ Before Showing to Evaluators

- [ ] Run `python app.py` - no errors
- [ ] Open http://localhost:5000 - page loads
- [ ] Click "Start Camera" - works
- [ ] Make gestures - detected correctly
- [ ] Database saves data - check table
- [ ] UI looks professional - responsive
- [ ] No console errors - browser console clear

---

## 🎯 Perfect For:

✅ College Projects (SGP/Mini Project)  
✅ Learning Full-Stack Development  
✅ Interview Portfolio  
✅ Learning Flask + OpenCV + React  
✅ Starting Point for Advanced Features  

---

**Ready to Impress Your Evaluators! 🚀**

Need help? Check README.md for detailed documentation!
