# Industrial Precision Design System

**Project**: Indian Railways Maintenance Planner (RailOpt)  
**ID**: `assets/1bcfb8bfe3274ed5908db14bc5c82ac4`  
**Primary Color**: `#003366` (Indian Railways Navy)  
**Theme**: Light  
**Typography**: Inter (Headlines & Body), JetBrains Mono (Data & Labels)  
**Roundness**: `0.25rem` (Soft / ROUND_FOUR)  

---

## Design System Specification (design.md)

```yaml
name: Industrial Precision
colors:
  surface: '#f6f9ff'
  surface-dim: '#d1dbe6'
  surface-bright: '#f6f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#ecf5ff'
  surface-container: '#e5effa'
  surface-container-high: '#dfe9f4'
  surface-container-highest: '#dae4ef'
  on-surface: '#131d24'
  on-surface-variant: '#43474f'
  inverse-surface: '#28313a'
  inverse-on-surface: '#e8f2fd'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#5a5f62'
  on-secondary: '#ffffff'
  secondary-container: '#dce0e4'
  on-secondary-container: '#5e6367'
  tertiary: '#141f2f'
  on-tertiary: '#ffffff'
  tertiary-container: '#293446'
  on-tertiary-container: '#919cb2'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#dfe3e7'
  secondary-fixed-dim: '#c3c7cb'
  on-secondary-fixed: '#171c1f'
  on-secondary-fixed-variant: '#43474b'
  tertiary-fixed: '#d8e3fa'
  tertiary-fixed-dim: '#bcc7dd'
  on-tertiary-fixed: '#111c2c'
  on-tertiary-fixed-variant: '#3c475a'
  background: '#f6f9ff'
  on-background: '#131d24'
  surface-variant: '#dae4ef'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 24px
  table-cell-padding: 8px 12px
```

---

## Brand & Style

The design system is engineered for **RailOpt**, a mission-critical maintenance planning tool for Indian Railways. The brand personality is authoritative, reliable, and precise, mirroring the institutional weight of one of the world's largest rail networks. 

The visual style is **Corporate / Modern** with an emphasis on **high-density data management**. It avoids decorative flourishes in favor of functional clarity. The UI prioritizes a "utilitarian aesthetic" where information hierarchy is established through structured grids and a disciplined use of color, ensuring that planners can manage complex block schedules without cognitive fatigue.

**Key Principles:**
- **Clarity over Visual Flair:** Every element must serve a functional purpose.
- **Operational Trust:** Uses a stable, navy-heavy palette to evoke safety and institutional permanence.
- **Density Optimized:** Compact spacing and typography to maximize the visibility of Gantt charts and tabular data.

## Colors

The palette is rooted in **Indian Railways Navy (#003366)**, used for primary actions, navigation sidebars, and branding. This provides a high-contrast anchor for the application.

- **Backgrounds:** Use `Professional White (#FFFFFF)` for primary content areas to ensure maximum legibility. `Muted Blue (#F0F4F8)` is reserved for secondary backgrounds, such as sidebar containers or dashboard card groupings.
- **Neutrals:** A range of grays (`#4A5568` for text, `#CBD5E0` for borders) maintains a soft but clear structure.
- **Functional Colors:** These are strictly reserved for operational status. **Critical Red** indicates conflicts or overdue maintenance; **Amber** signals warnings or tentative blocks; **Success Green** (used sparingly) indicates approved plans.

## Typography

The typography system uses **Inter** for its exceptional legibility in data-heavy environments. A secondary monospaced font, **JetBrains Mono**, is introduced specifically for IDs (Job IDs, Train Numbers) and time-stamps to ensure vertical alignment in tables and Gantt charts.

**Usage Guidelines:**
- **Headlines:** Keep titles concise. Use `headline-lg` for page headers and `headline-sm` for card titles.
- **Body:** `body-md` (14px) is the standard for all UI text to maintain high density without sacrificing readability.
- **Data Views:** Use `data-mono` for any numeric values, job identifiers, or time codes in tables to help users scan columns of data more efficiently.

## Layout & Spacing

This design system employs a **Fixed Grid** model for large desktop screens (common in control rooms), with a 12-column layout. 

**Layout Model:**
- **Sidebar:** Fixed width at 240px to ensure the navigation is always accessible but doesn't crowd the data space.
- **Gantt/Tables:** These components utilize a fluid container within the grid to maximize horizontal real estate.
- **Density:** We use a 4px base unit. For planning views, use "Compact" spacing (8px margins) to allow as much data on screen as possible. For dashboards, use "Comfortable" spacing (16px - 24px) to separate high-level metrics.

**Breakpoints:**
- **Desktop (L):** 1440px+ (Standard for planners)
- **Desktop (M):** 1280px (Standard laptops)
- **Tablet:** 768px (Sidebar collapses to icons-only).

## Elevation & Depth

To maintain a professional, flat enterprise look, the design system avoids heavy shadows. 

- **Surface Layers:** Hierarchy is achieved through **Tonal Layers**. The base background is white, while interactive areas like the sidebar or header use the Primary Navy or a light Muted Blue.
- **Cards:** Use a 1px border (#CBD5E0) instead of a shadow to define card boundaries.
- **Modals/Overlays:** Use a "Level 2" shadow—a tight, neutral shadow (0px 4px 6px rgba(0,0,0,0.05))—to lift the element off the page.
- **Gantt Bars:** No shadows. Use solid fills with high-contrast text to indicate the block status and department (Engineering, S&T, Traction).

## Shapes

The design system uses a **Soft (0.25rem)** roundedness level. This provides a modern touch while maintaining the structured, architectural feel required for an industrial application. 

- **Buttons & Inputs:** 4px (0.25rem) radius.
- **Dashboard Cards:** 8px (0.5rem) radius for a slightly softer container feel.
- **Gantt Bars:** 2px radius (near-sharp) to allow bars to sit flush against time-grid lines for precise visual measurement.

## Components

### Data Tables
- **Header:** Background #F8FAFC, bold Inter 12px text, uppercase.
- **Cells:** 13px Inter or JetBrains Mono. Use `table-cell-padding` for high-density.
- **Status Pills:** Small, rounded-full badges with subtle background tints and high-contrast text (e.g., Light Red background with Dark Red text for "Critical").

### Gantt Charts
- **Time Axis:** 12px labels, vertical grid lines every 60 minutes in #E2E8F0.
- **Block Bars:** Color-coded by department. Labels inside the bars should be 11px white text.
- **Conflict Markers:** A vertical red dashed line or a red stroke around overlapping blocks.

### Sidebar Navigation
- **Active State:** A vertical primary navy accent bar on the left with a subtle blue tint for the background of the active item.
- **Icons:** 20px size, stroke-based, consistent weight.

### Form Inputs
- **Style:** 1px border (#CBD5E0), white background. Focus state uses a 2px #003366 border.
- **Labels:** 12px bold, positioned above the input field.

### Operational Dashboard Cards
- **Value:** Large 24px-32px bold numbers.
- **Trend:** Small indicator (+/-) with status colors (Green/Red) to indicate changes in maintenance efficiency.
