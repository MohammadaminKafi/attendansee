# Django Admin Panel - Comprehensive Guide

## Overview
This guide documents the comprehensive Django admin panel configuration for the AttendanSee application, including all models from both the `authentication` and `attendance` apps.

---

## Authentication App

### User Admin

**Access:** `/admin/authentication/user/`

#### List Display
- Username
- Email
- Full Name
- Staff Status
- Active Status
- Superuser Status
- **Classes Count** - Number of classes owned (bold if > 0)
- Date Joined (formatted)
- Last Login (formatted)

#### Filters
- **Is Staff** - Staff/non-staff users
- **Is Active** - Active/inactive users
- **Is Superuser** - Superuser/regular users
- **Date Joined** - Filter by join date
- **Last Login** - Filter by last login
- **Groups** - Filter by user groups (only shows groups with users)

#### Search Fields
- Username
- Email
- First Name
- Last Name
- Class Names (searches in owned classes)

#### Custom Actions
1. **Activate Users** - Set `is_active=True` for selected users
2. **Deactivate Users** - Set `is_active=False` for selected users
3. **Make Staff** - Grant staff privileges to selected users
4. **Remove Staff** - Revoke staff privileges from selected users

#### Features
- Date hierarchy by join date
- 50 items per page
- Optimized queries with prefetch_related for classes
- Readonly fields: date_joined, last_login

---

## Attendance App

### Class Admin

**Access:** `/admin/attendance/class/`

#### List Display
- Name
- **Owner** (linked to User admin)
- **Students Count** (bold if > 0)
- **Sessions Count** (bold if > 0)
- Active Status (✓ Active / ✗ Inactive with colors)
- Created At (formatted)
- Updated At (formatted)

#### Filters
- **Is Active** - Active/inactive classes
- **Created At** - Filter by creation date
- **Updated At** - Filter by update date
- **Owner** - Filter by class owner (shows username and full name)

#### Search Fields
- Class name
- Description
- Owner username
- Owner email
- Owner first/last name

#### Inlines
- **Students** - Tabular inline showing enrolled students
- **Sessions** - Tabular inline showing class sessions

#### Custom Actions
1. **Activate Classes** - Set `is_active=True` for selected classes
2. **Deactivate Classes** - Set `is_active=False` for selected classes

#### Features
- Date hierarchy by creation date
- 50 items per page
- Optimized queries with annotations for counts
- Statistics section in detail view

---

### Student Admin

**Access:** `/admin/attendance/student/`

#### List Display
- Full Name (first + last)
- **Class** (linked to Class admin)
- Class Owner
- Student ID (or dash if empty)
- Email (or dash if empty)
- **Face Crops Count** (bold if > 0)
- Created At (formatted)

#### Filters
- **Class Enrolled** - Filter by specific class
- **Class Owner** - Filter by the owner of the class
- **Created At** - Filter by creation date
- **Has Email** - Yes/No filter
- **Has Student ID** - Yes/No filter

#### Search Fields
- First name
- Last name
- Student ID
- Email
- Class name
- Class owner username

#### Custom Actions
1. **Clear Email** - Remove email from selected students
2. **Clear Student ID** - Remove student ID from selected students

#### Features
- Date hierarchy by creation date
- 100 items per page
- Optimized queries with select_related and annotations
- Shows class owner for multi-tenant filtering

---

### Session Admin

**Access:** `/admin/attendance/session/`

#### List Display
- Name
- **Class** (linked to Class admin)
- Date (formatted)
- Time Range (start - end, or "From"/"Until" if partial)
- Processing Status (✓ Processed / ⧗ Pending with colors)
- **Images Count** (bold if > 0)
- **Progress** (X/Y images, percentage with color coding)
- Created At (formatted)

#### Filters
- **Is Processed** - Processed/unprocessed sessions
- **Date** - Filter by session date
- **Class** - Filter by specific class
- **Class Owner** - Filter by class owner
- **Created At** - Filter by creation date

#### Search Fields
- Session name
- Notes
- Class name
- Class owner username

#### Inlines
- **Images** - Tabular inline showing session images with face crop counts

#### Custom Actions
1. **Mark as Processed** - Set `is_processed=True` for selected sessions
2. **Mark as Unprocessed** - Set `is_processed=False` for selected sessions
3. **Update Processing Status** - Recalculate processing status based on images

#### Features
- Date hierarchy by session date
- 50 items per page
- Progress display with color coding:
  - Green: 100% processed
  - Orange: Partially processed
  - Red: 0% processed
- Optimized queries with annotations for image counts

---

### Image Admin

**Access:** `/admin/attendance/image/`

#### List Display
- ID
- **Session** (linked to Session admin)
- Class Name
- Original Path (truncated if > 50 chars)
- Processing Status (✓ Processed / ⧗ Pending with colors)
- **Face Crops Count** (bold if > 0)
- Upload Date (formatted)
- Processing Date (formatted or dash)

#### Filters
- **Is Processed** - Processed/unprocessed images
- **Upload Date** - Filter by upload date
- **Processing Date** - Filter by processing date
- **Session Class** - Filter by the class of the session
- **Class Owner** - Filter by class owner

#### Search Fields
- Original image path
- Processed image path
- Session name
- Class name

#### Inlines
- **Face Crops** - Tabular inline showing detected face crops

#### Custom Actions
1. **Mark as Processed** - Set `is_processed=True` and set processing_date to now
2. **Mark as Unprocessed** - Set `is_processed=False` and clear processing_date

#### Features
- Date hierarchy by upload date
- 50 items per page
- Path truncation for readability
- Optimized queries with select_related and annotations

---

### FaceCrop Admin

**Access:** `/admin/attendance/facecrop/`

#### List Display
- ID
- **Image** (linked to Image admin)
- Session Name
- Class Name
- **Student** (linked to Student admin, or dash if unidentified)
- Identification Status (✓ Identified / ✗ Unidentified with colors)
- **Confidence Score** (color coded: green ≥90%, orange ≥70%, red <70%)
- Created At (formatted)

#### Filters
- **Is Identified** - Identified/unidentified crops
- **Confidence Score** - Custom filter with ranges:
  - High (≥ 0.9)
  - Medium (0.7 - 0.9)
  - Low (< 0.7)
  - No Score
- **Created At** - Filter by creation date
- **Session Class** - Filter by class
- **Class Owner** - Filter by class owner

#### Search Fields
- Crop image path
- Coordinates
- Student first/last name
- Session name
- Class name

#### Detail View Fields
- Coordinates Display - Parsed coordinates (x, y, width, height)
- Crop Preview - Shows crop image path

#### Custom Actions
1. **Mark as Identified** - Set `is_identified=True` for selected crops
2. **Mark as Unidentified** - Set `is_identified=False` and clear student assignment
3. **Clear Student** - Remove student assignment and set `is_identified=False`

#### Features
- Date hierarchy by creation date
- 100 items per page
- Color-coded confidence scores
- Coordinates parsing in detail view
- Multi-level filtering through class hierarchy

---

## Key Features Across All Admins

### Performance Optimizations
1. **Select Related** - Reduces database queries for foreign keys
2. **Prefetch Related** - Optimizes many-to-many and reverse FK queries
3. **Annotations** - Counts calculated in database, not Python
4. **List Per Page** - Pagination configured per model

### User Experience
1. **Formatted Dates** - All dates displayed in readable format
2. **Color Coding** - Visual indicators for status (green/orange/red/gray)
3. **Icons** - Unicode icons for quick status recognition (✓, ✗, ⧗)
4. **Links** - Related objects linked for easy navigation
5. **Bold Counts** - Non-zero counts highlighted in bold
6. **Truncation** - Long paths truncated with "..." prefix

### Admin Actions
All actions provide user feedback via Django's message system:
- Success messages show count of affected objects
- Actions are accessible from list view

### Filtering Capabilities

#### Multi-Level Filtering
- Filter by class owner even for deeply nested models (FaceCrop → Image → Session → Class → Owner)
- Related-only filters show only values that exist in the database

#### Custom Filters
1. **OwnerFilter** - Shows all users who own classes
2. **ClassOwnerFilter** - Reusable filter for any model related to Class
3. **ConfidenceScoreFilter** - Range-based filtering for scores
4. **HasEmailFilter** - Boolean filter for email presence
5. **HasStudentIDFilter** - Boolean filter for student ID presence

#### Date Hierarchies
- User: By date_joined
- Class: By created_at
- Student: By created_at
- Session: By session date
- Image: By upload_date
- FaceCrop: By created_at

### Search Capabilities

#### Cross-Model Search
Most admins support searching across related models:
- Search students by class name
- Search images by session/class name
- Search face crops by student name

#### Field Coverage
Search includes:
- Text fields (names, descriptions, notes)
- Identifiers (username, email, student_id)
- Paths (image paths)
- Related object fields

---

## Usage Examples

### Example 1: Find All Unprocessed Images for a Specific Professor
1. Go to Image Admin
2. Filter by "Class Owner" → Select professor
3. Filter by "Is Processed" → No

### Example 2: Find High-Confidence Unidentified Face Crops
1. Go to FaceCrop Admin
2. Filter by "Is Identified" → No
3. Filter by "Confidence Score" → High (>= 0.9)

### Example 3: Bulk Activate Multiple Classes
1. Go to Class Admin
2. Select classes to activate
3. Choose "Activate selected classes" from Actions dropdown
4. Click "Go"

### Example 4: Track Session Processing Progress
1. Go to Session Admin
2. View "Progress" column to see X/Y images processed
3. Use "Update processing status" action to recalculate if needed

### Example 5: Find Students Without Email Addresses
1. Go to Student Admin
2. Filter by "Has Email" → No
3. Optionally filter by "Class" or "Class Owner" to narrow results

---

## Technical Notes

### Readonly Fields
The following fields are automatically set and cannot be edited:
- `created_at` - Auto-set on object creation
- `updated_at` - Auto-updated on object save
- `date_joined` - User registration date
- `last_login` - User's last login timestamp
- `upload_date` - Image upload timestamp
- Computed fields (counts, statistics)

### Fieldset Organization
All detail views organized into logical sections:
- **Basic Information** - Core fields
- **Status/Details** - Status flags and additional info
- **Statistics** - Computed fields (collapsed by default)
- **Timestamps** - Created/updated dates (collapsed by default)

### Inline Editing
Parent-child relationships shown via inlines:
- View/edit students and sessions directly from class detail
- View/edit images directly from session detail
- View/edit face crops directly from image detail

All inlines:
- Show change links to full detail view
- Have `extra=0` to not show empty forms by default
- Include most relevant fields for quick overview

---

## Color Coding Reference

### Status Colors
- **Green (✓)** - Active, Processed, Identified, High Confidence
- **Orange (⧗)** - Pending, Medium Confidence, Partial Progress
- **Red (✗)** - Inactive, Low Confidence, No Progress
- **Gray (✗)** - Unidentified, Neutral State

### Confidence Score Colors
- **Green** - ≥ 90% (High confidence)
- **Orange** - 70-89% (Medium confidence)
- **Red** - < 70% (Low confidence)

### Progress Colors
- **Green** - 100% processed
- **Orange** - 1-99% processed
- **Red** - 0% processed

---

## Best Practices

1. **Use Filters First** - Narrow down results before searching
2. **Leverage Date Hierarchy** - Quick navigation by time periods
3. **Check Statistics** - Use computed counts before diving into details
4. **Bulk Actions** - Save time by processing multiple objects at once
5. **Related Filters** - Use class owner filter to isolate data by professor
6. **Optimize Searches** - Specific searches across multiple fields work better than broad searches

---

## Future Enhancements

Potential additions (not yet implemented):
1. Image preview thumbnails in admin
2. Batch import/export functionality
3. Advanced reporting dashboard
4. Attendance summary views
5. Email notifications for processing completion
6. Audit log for changes
