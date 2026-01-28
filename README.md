# RPSU Anonymous Complaint Box - Flask Application

A modern, responsive Flask web application with **anonymous complaint submission**. Student identities are encrypted and never shown to administrators.

## 🎨 New Features

### ✨ Modern Responsive UI
- **Vibrant gradient backgrounds** with animated effects
- **Card-based design** for better mobile experience
- **Smooth animations** and micro-interactions
- **Fully responsive** - works perfectly on all devices
- **Modern color scheme** with purple-pink gradients

### 🔒 Anonymous & Secure
- **No personal data shown to admin** - Name, Student ID, and Email are encrypted
- Only **complaint details** visible to administrators
- Hash verification for identity (if needed for follow-up)
- Clear privacy notices for users

### 📊 Enhanced Admin Panel
- **Card-based complaint view** instead of table
- **Filter by status and priority**
- **Beautiful statistics dashboard**
- **Modern icons** using SVG
- **Better mobile experience**

## 🚀 Quick Start

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
**Only 2 packages needed:** Flask & Flask-SQLAlchemy

### 2️⃣ Run Application
```bash
python app.py
```

### 3️⃣ Access
- **Student Portal:** http://localhost:5000
- **Admin Dashboard:** http://localhost:5000/admin

## 📋 What's Different?

### Student Form
- ✅ Personal info section (encrypted, not shown to admin)
- ✅ Added **Category** field (Harassment, Discrimination, etc.)
- ✅ Clear privacy notice at top
- ✅ Better form layout with sections
- ✅ Custom radio buttons
- ✅ Improved mobile layout

### Admin Panel
- ✅ **No personal information displayed**
- ✅ Card-based layout (not table)
- ✅ Filter by status and priority
- ✅ Modern statistics cards with icons
- ✅ Better visual hierarchy
- ✅ Responsive grid layout

### Database Changes
**Removed fields:**
- ❌ name (encrypted in identity_hash)
- ❌ student_id (encrypted in identity_hash)
- ❌ email (encrypted in identity_hash)

**Added fields:**
- ✅ identity_hash (SHA-256 hash for verification)
- ✅ category (complaint category)

## 📱 Responsive Design

### Mobile (< 768px)
- Single column layout
- Stacked form fields
- Full-width cards
- Larger touch targets
- Optimized spacing

### Tablet (768px - 1024px)
- 2-column grid for complaints
- Responsive stats grid
- Comfortable spacing

### Desktop (> 1024px)
- Multi-column layouts
- Maximum content width: 1400px
- Optimal reading width for forms

## 🎨 Theme Customization

### Change Colors
Edit `static/css/style.css` (lines 1-25):
```css
:root {
    --primary: #6366f1;        /* Main purple */
    --primary-dark: #4f46e5;   /* Darker purple */
    --success: #10b981;        /* Green */
    --warning: #f59e0b;        /* Orange */
    --danger: #ef4444;         /* Red */
}
```

### Change Background Gradient
Edit `body` background in CSS:
```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

## 🔐 How Anonymous System Works

1. **Student submits complaint:**
   - Enters name, student ID, email (for verification)
   - Enters complaint details

2. **System processes:**
   - Creates SHA-256 hash of personal info
   - Stores **only the hash** in database
   - Original personal info is **never stored**

3. **Admin sees:**
   - Department, Category, Subject, Complaint text
   - Priority, Status, Date, Reference ID
   - **NO personal information**

4. **Identity verification (if needed):**
   - System can verify identity using hash
   - Cannot reverse hash to get original data
   - Provides anonymity while allowing verification

## 📊 Database Structure

```python
Complaint:
- id (Primary Key)
- reference_id (Unique tracking ID)
- identity_hash (SHA-256 hash - not shown)
- department (Shown to admin)
- category (Shown to admin)
- subject (Shown to admin)
- complaint (Shown to admin)
- priority (low/medium/high)
- status (pending/in_progress/resolved)
- created_at (Timestamp)
```

## 🔄 Migration from Old Database

If you have the old version, delete `complaints.db` and restart:
```bash
rm complaints.db
python app.py
```

The new database structure will be created automatically.

## 🌐 API Endpoints

### Public Routes
- `GET /` - Complaint submission form
- `POST /submit` - Submit anonymous complaint

### Admin Routes
- `GET /admin` - Dashboard with all complaints
- `GET /admin/complaint/<id>` - View complaint details
- `POST /admin/update_status/<id>` - Update complaint status

### API Routes
- `GET /api/complaints` - Get all complaints (JSON)
- `GET /api/stats` - Get statistics (JSON)

## 🎯 New Features in Detail

### Filter System
Admins can filter complaints by:
- **Status:** All / Pending / In Progress / Resolved
- **Priority:** All / High / Medium / Low

### Categories Available
- Harassment/Bullying
- Discrimination
- Infrastructure Issue
- Faculty Related
- Administrative Issue
- Financial Matter
- Academic Concern
- Safety/Security
- Other

### Status Workflow
1. **Pending** - Just submitted
2. **In Progress** - Being reviewed/handled
3. **Resolved** - Complaint resolved

## 🚀 Deployment

### For Production:

1. **Change Secret Key** in `app.py`:
```python
app.config['SECRET_KEY'] = 'your-super-secret-key-here'
```

2. **Use Production Database:**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host/db'
```

3. **Disable Debug Mode:**
```python
app.run(debug=False)
```

4. **Use Production Server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

5. **Add HTTPS** with nginx or Apache

## 📱 Browser Support

- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## ⚡ Performance

- **Optimized CSS** - Modern properties, hardware acceleration
- **Efficient animations** - CSS-only, no JavaScript overhead
- **Lazy loading** - Images and heavy content
- **Responsive images** - Proper sizing for devices
- **Minimal dependencies** - Only Flask + SQLAlchemy

## 🔧 Troubleshooting

### Old Database Issues
```bash
# Delete old database
rm complaints.db

# Restart app
python app.py
```

### Port Already in Use
```python
# Change port in app.py
app.run(port=5001)
```

### CSS Not Loading
- Clear browser cache (Ctrl+Shift+R)
- Check static folder structure
- Verify Flask is serving static files

### Mobile Layout Issues
- Check viewport meta tag in HTML
- Verify responsive CSS media queries
- Test on actual devices, not just browser resize

## 🎓 For Development

### Project Structure
```
rpsu-complaint-flask/
├── app.py                 # Main Flask application
├── requirements.txt       # Dependencies
├── complaints.db         # SQLite database (auto-created)
├── templates/            # HTML templates
│   ├── index.html       # Student complaint form
│   ├── admin.html       # Admin dashboard
│   └── view_complaint.html
└── static/              # Static files
    ├── css/
    │   └── style.css    # All styles (modern responsive)
    └── js/
        └── script.js    # Frontend JavaScript
```

### Adding New Features

**Add new category:**
Edit `templates/index.html`:
```html
<option value="new-category">New Category</option>
```

**Add admin authentication:**
```python
from flask_login import LoginManager, login_required

@app.route('/admin')
@login_required
def admin():
    # Your code
```

## 📝 License

Free to use and modify for educational purposes.

---

## 🎯 Quick Command Reference

```bash
# Install
pip install -r requirements.txt

# Run
python app.py

# Access
http://localhost:5000          # Student portal
http://localhost:5000/admin    # Admin dashboard

# Reset database
rm complaints.db && python app.py
```

**Built with Flask + Modern CSS for RPSU** 💜

---

**Key Improvement:** Complete anonymity while maintaining functionality! 🔒✨
