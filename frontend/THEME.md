# AttendanSee Frontend Theme Guide

## Overview
The AttendanSee frontend uses a **dark + emerald green** color palette with centralized theme configuration for consistent, maintainable styling.

## Theme System

### Centralized Configuration
All theme colors are defined in `src/styles/theme.ts`. Always import and use these constants instead of hardcoded Tailwind classes.

```typescript
import { theme } from '@/styles/theme';

// Example usage
<div className={theme.bg.card}>
  <button className={theme.interactive.primary}>
    Click me
  </button>
</div>
```

## Color Palette

### Primary Colors
- **Background**: `#0a0e12` (very dark blue-gray) - `bg-dark-bg`
- **Card**: `#111827` (dark gray) - `bg-dark-card`
- **Hover**: `#1f2937` (medium dark gray) - `bg-dark-hover`
- **Primary**: `#10b981` (emerald green) - `bg-primary`, `text-primary`, `border-primary`

### Text Colors
- **Primary**: `text-gray-100` (near white)
- **Secondary**: `text-gray-300` (light gray)
- **Tertiary**: `text-gray-400` (medium gray)
- **Muted**: `text-gray-500` (dim gray)

### Semantic Colors
- **Success**: `#10b981` (emerald green) - `text-success`, `bg-success`
- **Warning**: `#f59e0b` (amber) - `text-warning`, `bg-warning`
- **Danger**: `#ef4444` (red) - `text-danger`, `bg-danger`, `border-danger`

### Border Colors
- **Default**: `border-dark-border` (`#1f2937`)
- **Light**: `border-dark-border-light` (`#374151`)
- **Success**: `border-success`
- **Warning**: `border-warning`
- **Danger**: `border-danger`

## Component Styling Patterns

### Cards
```tsx
<div className="bg-dark-card border border-dark-border rounded-lg hover:border-primary transition-colors">
  {/* Card content */}
</div>
```

### Buttons
- Primary action: `bg-primary hover:bg-primary-dark text-white`
- Secondary: `bg-dark-card hover:bg-dark-hover border border-dark-border`
- Danger: `bg-danger hover:bg-danger-dark text-white`

### Input Fields
```tsx
<input className="bg-dark-card border border-dark-border text-gray-100 focus:ring-2 focus:ring-primary" />
```

### Icon Buttons (Minimal Style)
```tsx
<button className="p-1 hover:bg-dark-hover rounded text-gray-400 hover:text-primary transition-colors">
  <Icon size={16} />
</button>
```

### Tables
- Header: `bg-dark-card text-gray-300`
- Rows: `hover:bg-dark-hover`
- Borders: `border-dark-border`

## Design Principles

### 1. **Never use hardcoded slate/blue colors**
❌ Bad: `bg-slate-800`, `text-blue-500`  
✅ Good: `bg-dark-card`, `text-primary`

### 2. **Use semantic color names**
❌ Bad: `text-green-500` for success  
✅ Good: `text-success`

### 3. **Import from theme.ts for complex usage**
```typescript
import { theme, cn } from '@/styles/theme';

const className = cn(
  theme.bg.card,
  theme.border.default,
  theme.text.primary
);
```

### 4. **Consistent hover states**
- Cards: `hover:border-primary`
- Buttons: Background darkens
- Icons: Color changes to primary or danger

### 5. **Minimal icon buttons**
Use for edit/delete actions on rows:
```tsx
<button 
  onClick={handleEdit}
  className="p-1 hover:bg-dark-hover rounded text-gray-400 hover:text-primary transition-colors"
>
  <Edit2 size={16} />
</button>
```

## Common Patterns

### Modal Dialogs
```tsx
<Modal isOpen={show} onClose={close}>
  <form className="space-y-4">
    {/* Form content with theme colors */}
  </form>
</Modal>
```

### Status Badges
```tsx
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="danger">Error</Badge>
```

### Navigation
- Back buttons: Minimal icon + text style
- Breadcrumbs: `text-gray-500 hover:text-gray-300`
- Active links: `text-primary`

## Tailwind Configuration

Custom colors are defined in `tailwind.config.js`:

```javascript
colors: {
  primary: { DEFAULT: '#10b981', dark: '#059669', light: '#34d399' },
  success: '#10b981',
  warning: '#f59e0b',
  danger: { DEFAULT: '#ef4444', dark: '#dc2626', light: '#f87171' },
  'dark-bg': '#0a0e12',
  'dark-card': '#111827',
  'dark-hover': '#1f2937',
  'dark-border': '#1f2937',
  'dark-border-light': '#374151',
  'dark-light': '#374151',
}
```

## Utility Classes

### Spacing
- Gap: `gap-4`, `gap-6` (consistent spacing)
- Padding: `p-4`, `p-6` for cards
- Margin: `mb-4`, `mb-6` for sections

### Transitions
- Standard: `transition-colors` (200ms)
- Fast: `transition-all duration-150`
- Slow: `transition-opacity duration-300`

### Shadows
- Cards: `shadow-sm` on hover
- Modals: `shadow-xl`

## File Structure

```
frontend/src/
├── styles/
│   ├── theme.ts          # Centralized theme configuration
│   └── index.css         # Tailwind imports + custom utilities
├── components/
│   └── ui/               # Themed UI components
│       ├── Badge.tsx
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Table.tsx
│       └── ...
└── pages/                # Page components using theme
```

## Migration Checklist

When updating old code to use the theme:

- [ ] Replace all `bg-slate-*` with `bg-dark-*`
- [ ] Replace all `text-slate-*` with `text-gray-*`
- [ ] Replace all `border-slate-*` with `border-dark-*`
- [ ] Replace all `bg-blue-*` with `bg-primary`
- [ ] Replace all `text-blue-*` with `text-primary`
- [ ] Replace all `text-green-*` with `text-success`
- [ ] Replace all `text-yellow-*` with `text-warning`
- [ ] Replace all direct red colors with danger theme
- [ ] Update hover states to use `hover:bg-dark-hover`
- [ ] Update focus rings to use `focus:ring-primary`

## Examples

### Before (Inconsistent)
```tsx
<div className="bg-slate-800 border border-slate-700">
  <button className="bg-blue-600 hover:bg-blue-700">
    Click
  </button>
  <span className="text-red-400">Error</span>
</div>
```

### After (Consistent)
```tsx
<div className="bg-dark-card border border-dark-border">
  <button className="bg-primary hover:bg-primary-dark">
    Click
  </button>
  <span className="text-danger">Error</span>
</div>
```

## Resources

- Tailwind Config: `tailwind.config.js`
- Theme Constants: `src/styles/theme.ts`
- Custom Styles: `src/styles/index.css`
- Lucide Icons: https://lucide.dev/icons/

---

**Remember**: Always use the centralized theme for consistency and easier future updates!
