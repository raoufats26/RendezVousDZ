# 🔧 HOW TO ADD GLOBAL THEME + LANGUAGE CONTROLS

## What you get
A floating widget (bottom-right corner) on **every page** with:
- 🌙 / ☀️ Dark/Light mode toggle
- EN / FR / ع language switcher

---

## Step 1 — Copy the file
Put `global_controls.js` in your static folder:
```
/static/global_controls.js
```

## Step 2 — Add ONE script tag to your base template
In your `templates/base.html` (or wherever your `<body>` ends), add this line
**AFTER** the `main.js` script tag:

```html
<script src="{{ url_for('static', filename='global_controls.js') }}"></script>
```

Example (bottom of base.html):
```html
    <script src="{{ url_for('static', filename='main.js') }}"></script>
    <script src="{{ url_for('static', filename='global_controls.js') }}"></script>
</body>
</html>
```

**That's it.** The widget auto-injects itself on every page.

---

## Step 3 — Hide it on the digital display page (optional)
The display page already has `display-page` hidden via CSS.
If your `display.html` has `<body class="display-body">`, add this to it:
```html
<body class="display-body display-page">
```
The widget will automatically hide itself on that page.

---

## How language switching works
The switcher uses `data-i18n` attributes on HTML elements.
Any element with `data-i18n="key"` gets translated automatically when switching.

Example in your templates:
```html
<button data-i18n="addToQueue">Add to Queue</button>
<input data-i18n-placeholder="clientNamePlaceholder" placeholder="Client Name">
```

For **server-rendered text** (Jinja2 output), you need to wrap it in a span with the key:
```html
<span data-i18n="todaysQueue">Today's Queue</span>
```

---

## Troubleshooting
- **Widget not showing?** Make sure the script tag is inside `<body>`, not `<head>`
- **Language not persisting?** It saves to localStorage automatically — no server needed
- **Theme flash on load?** Make sure `global_controls.js` loads before `</body>` 
  (or move it to `<head>` with `defer` attribute)
- **Charts not rebuilding in dark mode?** Already handled — uses `buildCharts()` if present
