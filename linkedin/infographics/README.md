# Infographics / LinkedIn

## JPG (ready to upload)

Folder: **`jpg/`**

| File | Use |
|------|-----|
| `01-oblozhka-linkedin.jpg` | Article cover (1200x644) |
| `02-uravnenie-uspeha.jpg` | Diagnostics + chemistry |
| `03-vybor-tehnologii.jpg` | Decision tree |
| `04-tri-tehnologii.jpg` | RPM / gel / RPPG |
| `05-hemoinformatika.jpg` | Chemoinformatics |
| `06-cheklist-lidera.jpg` | 5-step checklist |

## Regenerate

```bash
python export_jpg.py
```

Creates fixed UTF-8 SVG files and JPG exports (Playwright, 2x scale, quality 92%).

## Preview

Open `preview.html` in browser for SVG preview.

## Source script

`export_jpg.py` — all Russian text via Unicode escapes (no encoding corruption).
