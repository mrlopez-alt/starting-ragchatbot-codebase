# Frontend Changes: Dark/Light Theme Toggle

## Summary
Added a toggle button (top-right) that switches the UI between the existing dark theme and a new light theme. Theme switching is driven by CSS custom properties and a `data-theme` attribute on the `<html>` element.

## Files changed

### `frontend/index.html`
- Inline script in `<head>` sets `data-theme` on `<html>` **before first paint** (saved choice in `localStorage`, else the OS `prefers-color-scheme`, else dark). Prevents a flash of the wrong theme.
- New `<button id="themeToggle" class="theme-toggle">` at the top of `<body>` with sun and moon SVG icons (`aria-hidden`), `aria-label`, `title` and `aria-pressed`.
- Cache-busting versions bumped (`style.css?v=10`, `script.js?v=10`).

### `frontend/style.css`
- **New variables** on `:root` (dark values) so previously hardcoded colors are themeable: `--code-bg`, `--welcome-shadow`, `--button-shadow`, `--error-bg/-text/-border`, `--success-bg/-text/-border`, plus `color-scheme: dark`.
- **Light theme** block `:root[data-theme="light"]`: light backgrounds (`#f8fafc` / `#ffffff`), dark text (`#0f172a` primary, `#475569` secondary — both pass WCAG AA on white), `#e2e8f0` borders, same blue primary (`#2563eb`, 5.2:1 on white), darker error/success text for contrast, softer shadows, `color-scheme: light` (native scrollbars/form controls).
- Hardcoded colors in code blocks, welcome message, send-button hover, error and success messages replaced by the variables above.
- Bug fix: blockquote used undefined `var(--primary)`; now `var(--primary-color)`.
- **Smooth transition**: `html.theme-transition *` animates background, color, border and shadow for 0.3s. The class is added only while switching, so it doesn't interfere with existing hover/transform transitions.
- **`.theme-toggle` styles**: fixed 44×44 circular button in the top-right, uses surface/border tokens, hover lift, visible `:focus-visible` ring. Sun/moon icons cross-fade with a rotate+scale animation (the sun shows in dark mode, the moon in light mode).
- `prefers-reduced-motion: reduce` disables the toggle and theme transitions.

### `frontend/script.js`
- `setupThemeToggle()` (called on `DOMContentLoaded`) wires the click handler and syncs the labels.
- `toggleTheme()` / `setTheme(theme)`: updates `data-theme`, adds `theme-transition` for 350 ms, updates `aria-label`/`title`/`aria-pressed`, and saves the choice in `localStorage` (wrapped in try/catch).

## Accessibility
- Native `<button>`: reachable with Tab, activates with Enter/Space.
- The label always describes the action ("Switch to light theme" / "Switch to dark theme").
- Visible focus ring for keyboard users only (`:focus-visible`).
- Text contrast in both themes meets WCAG AA.
