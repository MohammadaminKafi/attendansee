# Django Admin - Quick Reference Card

## Admin URLs

| Model | URL |
|-------|-----|
| Users | `/admin/authentication/user/` |
| Classes | `/admin/attendance/class/` |
| Students | `/admin/attendance/student/` |
| Sessions | `/admin/attendance/session/` |
| Images | `/admin/attendance/image/` |
| Face Crops | `/admin/attendance/facecrop/` |

---

## Quick Filter Guide

### Find All Items for a Specific Professor
**Filter:** Class Owner → Select professor name

**Available in:**
- Students
- Sessions
- Images
- Face Crops

### Find Unprocessed Items
**Filter:** Is Processed → No

**Available in:**
- Sessions
- Images

### Find Unidentified Face Crops
**Filter:** Is Identified → No

**Available in:**
- Face Crops

### Find High Confidence Unidentified Faces
**Filters:**
1. Is Identified → No
2. Confidence Score → High (>= 0.9)

**Available in:**
- Face Crops

### Find Students Without Email/ID
**Filter:** Has Email → No (or Has Student ID → No)

**Available in:**
- Students

---

## Quick Action Guide

### Bulk Activate/Deactivate
1. Select items
2. Choose action: "Activate..." or "Deactivate..."
3. Click "Go"

**Available for:**
- Users
- Classes

### Mark as Processed
1. Select items
2. Choose: "Mark as processed"
3. Click "Go"

**Available for:**
- Sessions
- Images

### Clear Student Assignment
1. Select face crops
2. Choose: "Clear student assignment"
3. Click "Go"

**Available for:**
- Face Crops

---

## Color Coding

| Color | Meaning |
|-------|---------|
| 🟢 Green (✓) | Active, Processed, Identified, High Confidence (≥90%) |
| 🟠 Orange (⧗) | Pending, Medium Confidence (70-89%) |
| 🔴 Red (✗) | Inactive, Low Confidence (<70%) |
| ⚪ Gray (✗) | Unidentified |

---

## List Display Highlights

### User Admin
- Shows classes count
- Shows last login
- Color-coded status

### Class Admin
- Shows students count
- Shows sessions count
- Shows owner with link
- Active/inactive status

### Student Admin
- Shows full name
- Shows class owner
- Shows face crops count
- Links to class

### Session Admin
- Shows processing progress (X/Y images)
- Shows time range
- Shows images count
- Color-coded status

### Image Admin
- Shows session and class
- Shows face crops count
- Shows processing dates
- Truncated paths

### FaceCrop Admin
- Shows student (linked)
- Shows session and class
- Color-coded confidence score
- Identified/unidentified status

---

## Search Tips

### Cross-Model Search
You can search related objects:
- Search students by class name
- Search images by session name
- Search face crops by student name

### Multiple Fields
Search works across multiple fields simultaneously:
- Student search: first name, last name, ID, email, class name
- User search: username, email, first name, last name, class names

---

## Inline Editing

### Class Detail View
- Edit students inline
- Edit sessions inline
- Add new students/sessions without leaving class page

### Session Detail View
- Edit images inline
- See face crop count per image
- Add new images without leaving session page

### Image Detail View
- Edit face crops inline
- See identified students
- Link crops to students

---

## Performance Tips

1. **Use Filters First** - Narrow results before searching
2. **Date Hierarchy** - Navigate by time periods efficiently
3. **Bulk Actions** - Process multiple items at once
4. **Statistics in List** - Check counts before opening details

---

## Common Workflows

### Workflow 1: Review Unprocessed Sessions
```
1. Go to Session Admin
2. Filter: Is Processed → No
3. Sort by date
4. Open each session
5. Check images inline
6. Mark as processed when ready
```

### Workflow 2: Identify Face Crops
```
1. Go to FaceCrop Admin
2. Filter: Is Identified → No
3. Optional: Filter by Confidence Score → High
4. Open each crop
5. Assign to student
6. Save
```

### Workflow 3: Manage Class Roster
```
1. Go to Class Admin
2. Find your class
3. Open class detail
4. Add/edit students in inline section
5. Save
```

### Workflow 4: Check Student Attendance
```
1. Go to Student Admin
2. Search for student name
3. Open student detail
4. See face crops count
5. Click face crop count to see all detections
```

### Workflow 5: Bulk Deactivate Old Classes
```
1. Go to Class Admin
2. Filter by date range (old classes)
3. Select classes to deactivate
4. Action: "Deactivate selected classes"
5. Click "Go"
```

---

## Keyboard Shortcuts (Standard Django)

| Key | Action |
|-----|--------|
| `s` | Save and continue editing |
| `Ctrl+s` | Save |
| `Esc` | Cancel/close |

---

## Best Practices

✅ **DO:**
- Use filters to narrow results before searching
- Check statistics columns for overview
- Use bulk actions for efficiency
- Navigate via links between related objects
- Use date hierarchy for time-based navigation

❌ **DON'T:**
- Broad searches without filters (slow)
- Edit many objects one by one (use bulk actions)
- Forget to save changes
- Delete without checking relationships

---

## Quick Statistics

### Where to Find Counts

| Admin | Shows Count Of |
|-------|----------------|
| User | Classes owned |
| Class | Students enrolled, Sessions created |
| Student | Face crops detected |
| Session | Images uploaded, Processing progress |
| Image | Face crops detected |

All counts are **bold** if greater than zero!

---

## Documentation

📚 **Full Guide:** `backend/attendance/docs/ADMIN_PANEL_GUIDE.md`
📊 **Implementation Summary:** `backend/ADMIN_IMPLEMENTATION_SUMMARY.md`

---

## Need Help?

1. Check the full ADMIN_PANEL_GUIDE.md for detailed explanations
2. Hover over field labels in admin for help text
3. Check Django admin documentation: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
