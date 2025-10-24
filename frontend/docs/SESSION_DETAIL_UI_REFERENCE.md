# Session Detail Page - UI Layout

## Page Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Breadcrumb: Classes > Class Name > Session Name                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SESSION INFO CARD                                         │ │
│  │                                                           │ │
│  │  Session Name                            [Status Badge]  │ │
│  │  Date: 01/15/2024  Start: 10:00  End: 11:30            │ │
│  │                                                           │ │
│  │  Notes: [Session notes displayed here...]               │ │
│  │                                                           │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                │ │
│  │  │ Images  │  │ Faces   │  │Identified│                │ │
│  │  │   12    │  │   45    │  │   38     │                │ │
│  │  └─────────┘  └─────────┘  └─────────┘                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ IMAGES CARD                                               │ │
│  │                                                           │ │
│  │  Images                              [Upload Images]     │ │
│  │  12 / 20 images uploaded                                 │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │ IMAGE GRID (Responsive 2-5 columns)             │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐       │   │ │
│  │  │  │img1│  │img2│  │img3│  │img4│  │img5│       │   │ │
│  │  │  │ ●  │  │ ●  │  │ ●  │  │ ●  │  │ ●  │       │   │ │
│  │  │  └────┘  └────┘  └────┘  └────┘  └────┘       │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐       │   │ │
│  │  │  │img6│  │img7│  │img8│  │img9│  │img10│      │   │ │
│  │  │  │ ●  │  │ ●  │  │ ●  │  │ ●  │  │ ●  │       │   │ │
│  │  │  └────┘  └────┘  └────┘  └────┘  └────┘       │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌────┐  ┌────┐                                │   │ │
│  │  │  │img11│ │img12│                               │   │ │
│  │  │  │ ●  │  │ ●  │                                │   │ │
│  │  │  └────┘  └────┘                                │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Image Card (Hover State)

```
┌──────────────────────┐
│                      │
│   [Image Preview]    │  ← Image fills this space
│                      │
│ ┌──────────────────┐ │
│ │ Gradient Overlay │ │  ← Appears on hover
│ │                  │ │
│ │ [✓ Processed] [🗑]│ │  ← Status badge + Delete button
│ │                  │ │
│ │ 🕐 Jan 15, 10:30 │ │  ← Upload time
│ │ 3 faces detected │ │  ← Face count
│ └──────────────────┘ │
│  ●                   │  ← Status dot (always visible)
└──────────────────────┘    Green=Processed, Yellow=Pending
```

## Image Card States

### Normal State
- Square aspect ratio
- Image preview displayed
- Small status dot in top-right corner
- Minimal border
- Hover state: border color changes

### Hover State
- Gradient overlay from bottom
- Status badge visible
- Delete button visible
- Upload time visible
- Face count visible
- Increased brightness

### Empty State
```
┌─────────────────────────────────┐
│                                 │
│         [Upload Icon]           │
│                                 │
│    No images uploaded yet       │
│   Upload images to start        │
│       processing                │
│                                 │
└─────────────────────────────────┘
```

## Responsive Breakpoints

| Screen Size | Columns | Example                           |
|------------|---------|-----------------------------------|
| Mobile     | 2       | `grid-cols-2`                    |
| Small      | 3       | `sm:grid-cols-3`                 |
| Medium     | 4       | `md:grid-cols-4`                 |
| Large      | 5       | `lg:grid-cols-5`                 |

## Color Scheme (Dark Theme)

- **Background**: `#0f172a` (slate-950)
- **Cards**: `#1e293b` (slate-800)
- **Borders**: `#334155` (slate-700)
- **Text Primary**: `#ffffff` (white)
- **Text Secondary**: `#cbd5e1` (slate-300)
- **Text Tertiary**: `#94a3b8` (slate-400)
- **Primary (Blue)**: `#3b82f6` (blue-500)
- **Success (Green)**: `#22c55e` (green-500)
- **Warning (Yellow)**: `#eab308` (yellow-500)
- **Danger (Red)**: `#ef4444` (red-500)

## Interactive Elements

### Upload Button
```
┌──────────────────────┐
│ 📤 Upload Images     │  ← Normal state
└──────────────────────┘

┌──────────────────────┐
│ 📤 Uploading...      │  ← Uploading state (disabled)
└──────────────────────┘

┌──────────────────────┐
│ 📤 Upload Images     │  ← Disabled state (20/20)
└──────────────────────┘    Grayed out
```

### Status Badges
```
┌───────────────┐
│ ✓ Processed   │  Green badge
└───────────────┘

┌───────────────┐
│ ✗ Pending     │  Yellow badge
└───────────────┘
```

### Delete Button
```
┌────┐
│ 🗑 │  Red background, white icon
└────┘  Hover: Brighter red
```

## Navigation Flow

```
Classes Page
    │
    └─> Class Detail Page (click class card)
            │
            └─> Sessions Tab
                    │
                    └─> Session Detail Page (click session row)
                            │
                            ├─> View images
                            ├─> Upload images
                            └─> Delete images
```

## Keyboard/Mouse Interactions

1. **Session Table Row**: Click anywhere on row → Navigate to session detail
2. **Upload Button**: Click → Opens file picker (multiple selection enabled)
3. **Image Card**: Hover → Shows overlay with details
4. **Delete Button**: Click → Shows confirmation dialog → Deletes image
5. **Breadcrumb**: Click any item → Navigate to that page

## Limit Warnings

### Approaching Limit (18-19 images)
```
ℹ️ You can upload 2 more images (20 image limit)
```

### At Limit (20 images)
```
⚠️ Maximum image limit reached (20 images)
```

### Upload Attempt Exceeds Limit
```
⚠️ Only 5 images uploaded. Maximum 20 images per session.
```
(If user tries to upload 10 files but only 5 slots remain)

## Error States

### Load Error
```
❌ Failed to load session data
```

### Upload Error
```
❌ Failed to upload one or more images
```

### Delete Error
```
❌ Failed to delete image
```

## Loading States

### Page Load
```
  [Spinner Animation]
```

### Upload in Progress
```
[Upload Images]  →  [Uploading...]  →  [Upload Images]
   (Enabled)         (Disabled)          (Enabled)
```

## Data Display Formats

- **Date**: `Jan 15, 2024`
- **Time**: `10:30 AM`
- **DateTime**: `Jan 15, 2024, 10:30 AM`
- **Counts**: `12`, `45`, `38` (plain numbers)
- **Status**: `Processed`, `Pending` (badges)
- **Face Count**: `3 faces detected` (or `1 face detected`)
