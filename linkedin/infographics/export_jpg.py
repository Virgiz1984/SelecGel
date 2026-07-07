# -*- coding: utf-8 -*-
"""Generate SVG infographics and export to JPG via Playwright."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).parent
JPG_DIR = OUT / "jpg"

# All labels via unicode escapes (encoding-safe)
L = {
    "skv": "\u0441\u043a\u0432\u0430\u0436\u0438\u043d\u0430",
    "hdr": "\u041d\u0415\u0424\u0422\u0415\u0414\u041e\u0411\u042b\u0427\u0410 \u00b7 \u041e\u0413\u0420\u0410\u041d\u0418\u0427\u0415\u041d\u0418\u0415 \u0412\u041e\u0414\u041e\u041f\u0420\u0418\u0422\u041e\u041a\u0410",
    "t1": "\u0421\u0435\u043b\u0435\u043a\u0442\u0438\u0432\u043d\u043e\u0435 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0435 \u0432\u043e\u0434\u043e\u043f\u0440\u0438\u0442\u043e\u043a\u0430",
    "t2": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u2014 \u0434\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430. \u041f\u043e\u0442\u043e\u043c \u2014 \u0440\u0435\u0430\u0433\u0435\u043d\u0442.",
    "sub1": "RPM \u00b7 \u0433\u0435\u043b\u0438 \u00b7 PPG \u00b7 \u0445\u0435\u043c\u043e\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0442\u0438\u043a\u0430 \u00b7 core flood",
    "rpm_w": "RPM-\u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043e\u043a \u0432 \u043c\u0438\u0440\u0435",
    "obv": "\u0442\u0438\u043f\u0438\u0447\u043d\u0430\u044f \u043e\u0431\u0432\u043e\u0434\u043d\u0451\u043d\u043d\u043e\u0441\u0442\u044c",
    "f1": "#1 \u0444\u0430\u043a\u0442\u043e\u0440 \u2014 candidate selection",
    "foot": "\u0421\u0442\u0430\u0442\u044c\u044f \u0434\u043b\u044f LinkedIn \u00b7 vodopritok project",
    "eq_t": "\u0423\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u0443\u0441\u043f\u0435\u0448\u043d\u043e\u0433\u043e \u041e\u0412\u041f",
    "eq_s": "\u041d\u0435 \u00ab\u043a\u0430\u043a\u043e\u0439 \u0440\u0435\u0430\u0433\u0435\u043d\u0442 \u043a\u0443\u043f\u0438\u0442\u044c\u00bb, \u0430 \u00ab\u0447\u0442\u043e \u0438\u043c\u0435\u043d\u043d\u043e \u043b\u0435\u0447\u0438\u043c\u00bb",
    "diag": "\u0414\u0418\u0410\u0413\u041d\u041e\u0421\u0422\u0418\u041a\u0410",
    "chim": "\u0425\u0418\u041c\u0418\u042f",
    "eff": "\u042d\u0424\u0424\u0415\u041a\u0422",
    "eq_f": "\u0425\u0438\u043c\u0438\u044f \u2014 \u043f\u043e\u043b\u043e\u0432\u0438\u043d\u0430 \u0443\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u044f. \u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430 \u2014 \u0432\u0442\u043e\u0440\u0430\u044f.",
    "dt_t": "\u041a\u0430\u043a\u043e\u0439 \u043c\u0435\u0445\u0430\u043d\u0438\u0437\u043c \u043e\u0431\u0432\u043e\u0434\u043d\u0435\u043d\u0438\u044f \u2014 \u0442\u0430\u043a\u0430\u044f \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f",
    "dt_root": "\u041e\u0442\u043a\u0443\u0434\u0430 \u0432\u043e\u0434\u0430 \u0432 \u0441\u043a\u0432\u0430\u0436\u0438\u043d\u0435?",
    "dt_foot": "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043c\u0435\u0445\u0430\u043d\u0438\u0437\u043c \u2192 \u043f\u043e\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441 \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0438",
    "tri_t": "3 \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0438, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u0441\u0442\u043e\u0438\u0442 \u0437\u043d\u0430\u0442\u044c",
    "tri_s": "\u0414\u0430\u0436\u0435 \u0435\u0441\u043b\u0438 \u0432\u044b \u043d\u0435 \u0445\u0438\u043c\u0438\u043a",
    "gel": "\u0422\u0435\u0440\u043c\u043e\u0442\u0440\u043e\u043f\u043d\u044b\u0439 \u0433\u0435\u043b\u044c",
    "ok_r": "\u2713 \u0420\u0430\u0431\u043e\u0442\u0430\u0435\u0442:",
    "no_r": "\u2717 \u041d\u0435 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442:",
    "hem_t": "\u0425\u0435\u043c\u043e\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0442\u0438\u043a\u0430: 100 \u0440\u0435\u0446\u0435\u043f\u0442\u0443\u0440 \u2192 15",
    "hem_s": "\u0424\u0438\u043b\u044c\u0442\u0440 \u043f\u0435\u0440\u0435\u0434 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u0435\u0439",
    "chk_t": "\u0427\u0435\u043a\u043b\u0438\u0441\u0442 \u043b\u0438\u0434\u0435\u0440\u0430 \u043f\u0440\u043e\u0435\u043a\u0442\u0430 \u041e\u0412\u041f",
    "chk_s": "5 \u0448\u0430\u0433\u043e\u0432 \u0431\u0435\u0437 \u0431\u044e\u0440\u043e\u043a\u0440\u0430\u0442\u0438\u0438",
}


def svg01() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 644" width="1200" height="644">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B1F3A"/><stop offset="55%" stop-color="#123456"/><stop offset="100%" stop-color="#1A4D6E"/>
    </linearGradient>
    <linearGradient id="oil" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#F4C542"/><stop offset="100%" stop-color="#C8860A"/></linearGradient>
    <linearGradient id="water" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#5BC0EB"/><stop offset="100%" stop-color="#2E86AB"/></linearGradient>
  </defs>
  <rect width="1200" height="644" fill="url(#bg)"/>
  <circle cx="980" cy="120" r="180" fill="#fff" opacity="0.04"/>
  <circle cx="1050" cy="520" r="240" fill="#fff" opacity="0.03"/>
  <g transform="translate(780,90)">
    <rect x="70" y="0" width="36" height="420" fill="#334155" rx="4"/>
    <rect x="78" y="180" width="20" height="160" fill="url(#water)" opacity="0.9"/>
    <rect x="78" y="250" width="20" height="90" fill="url(#oil)" opacity="0.95"/>
    <path d="M88 420 L60 470 L116 470 Z" fill="#475569"/>
    <text x="88" y="505" text-anchor="middle" fill="#94A3B8" font-family="Arial,sans-serif" font-size="14">{L["skv"]}</text>
  </g>
  <text x="80" y="120" fill="#FFF" font-family="Arial,sans-serif" font-size="22" letter-spacing="2">{L["hdr"]}</text>
  <text x="80" y="200" fill="#FFF" font-family="Arial,sans-serif" font-size="44" font-weight="bold">{L["t1"]}</text>
  <text x="80" y="260" fill="#F4C542" font-family="Arial,sans-serif" font-size="36" font-weight="bold">{L["t2"]}</text>
  <text x="80" y="310" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="22">{L["sub1"]}</text>
  <g transform="translate(80,390)"><rect width="210" height="56" rx="28" fill="#fff" opacity="0.12"/>
    <text x="24" y="35" fill="#FFF" font-family="Arial,sans-serif" font-size="20" font-weight="bold">3000+</text>
    <text x="92" y="35" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="18">{L["rpm_w"]}</text></g>
  <g transform="translate(320,390)"><rect width="250" height="56" rx="28" fill="#fff" opacity="0.12"/>
    <text x="24" y="35" fill="#FFF" font-family="Arial,sans-serif" font-size="20" font-weight="bold">85%</text>
    <text x="82" y="35" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="18">{L["obv"]}</text></g>
  <g transform="translate(600,390)"><rect width="280" height="56" rx="28" fill="#E8A838" opacity="0.95"/>
    <text x="24" y="35" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="18" font-weight="bold">{L["f1"]}</text></g>
  <text x="80" y="590" fill="#64748B" font-family="Arial,sans-serif" font-size="16">{L["foot"]}</text>
</svg>'''


def svg02() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="1200" height="675">
  <rect width="1200" height="675" fill="#F8FAFC"/>
  <text x="600" y="70" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="36" font-weight="bold">{L["eq_t"]}</text>
  <text x="600" y="110" text-anchor="middle" fill="#64748B" font-family="Arial,sans-serif" font-size="20">{L["eq_s"]}</text>
  <rect x="60" y="170" width="320" height="360" rx="20" fill="#E8F4FC" stroke="#2E86AB" stroke-width="3"/>
  <circle cx="220" cy="230" r="42" fill="#2E86AB"/><text x="220" y="242" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="32" font-weight="bold">1</text>
  <text x="220" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="28" font-weight="bold">{L["diag"]}</text>
  <text x="90" y="360" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 PLT / \u0442\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u043d\u044b\u0439 \u043f\u0440\u043e\u0444\u0438\u043b\u044c</text>
  <text x="90" y="395" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 \u0418\u0441\u0442\u043e\u0440\u0438\u044f \u0434\u0435\u0431\u0438\u0442\u043e\u0432 \u043d\u0435\u0444\u0442\u0438/\u0432\u043e\u0434\u044b</text>
  <text x="90" y="430" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 Tracers, cross-flow</text>
  <text x="90" y="465" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 \u041c\u0435\u0445\u0430\u043d\u0438\u0437\u043c: coning / channel</text>
  <text x="430" y="370" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="72" font-weight="bold">+</text>
  <rect x="460" y="170" width="320" height="360" rx="20" fill="#FFF8E7" stroke="#C8860A" stroke-width="3"/>
  <circle cx="620" cy="230" r="42" fill="#C8860A"/><text x="620" y="242" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="32" font-weight="bold">2</text>
  <text x="620" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="28" font-weight="bold">{L["chim"]}</text>
  <text x="490" y="360" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 RPM \u2014 \u0444\u0430\u0437\u043e\u0432\u0430\u044f \u0441\u0435\u043b\u0435\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c</text>
  <text x="490" y="395" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 \u0413\u0435\u043b\u0438 / PPG/RPPG</text>
  <text x="490" y="430" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 \u0420\u0435\u0446\u0435\u043f\u0442\u0443\u0440\u0430 \u043f\u043e\u0434 \u043f\u043b\u0430\u0441\u0442</text>
  <text x="490" y="465" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2022 Core flood gate \u043f\u0435\u0440\u0435\u0434 \u043f\u043e\u043b\u0435\u043c</text>
  <text x="830" y="370" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="72" font-weight="bold">=</text>
  <rect x="860" y="170" width="280" height="360" rx="20" fill="#E8F8EE" stroke="#16A34A" stroke-width="3"/>
  <circle cx="1000" cy="230" r="42" fill="#16A34A"/><text x="1000" y="248" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="28" font-weight="bold">OK</text>
  <text x="1000" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="26" font-weight="bold">{L["eff"]}</text>
  <text x="890" y="370" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2193 \u043e\u0431\u0432\u043e\u0434\u043d\u0451\u043d\u043d\u043e\u0441\u0442\u044c</text>
  <text x="890" y="410" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2192 \u0434\u0435\u0431\u0438\u0442 \u043d\u0435\u0444\u0442\u0438</text>
  <text x="890" y="450" fill="#334155" font-family="Arial,sans-serif" font-size="18">\u2193 OPEX \u043f\u043e\u0434\u044a\u0451\u043c\u0430</text>
  <rect x="120" y="570" width="960" height="70" rx="12" fill="#0B1F3A"/>
  <text x="600" y="615" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{L["eq_f"]}</text>
</svg>'''


def svg03() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 720" width="1200" height="720">
  <rect width="1200" height="720" fill="#F8FAFC"/>
  <text x="600" y="55" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="34" font-weight="bold">{L["dt_t"]}</text>
  <rect x="420" y="100" width="360" height="70" rx="35" fill="#0B1F3A"/>
  <text x="600" y="143" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{L["dt_root"]}</text>
  <line x1="600" y1="170" x2="200" y2="230" stroke="#94A3B8" stroke-width="2"/>
  <line x1="600" y1="170" x2="600" y2="230" stroke="#94A3B8" stroke-width="2"/>
  <line x1="600" y1="170" x2="1000" y2="230" stroke="#94A3B8" stroke-width="2"/>
  <rect x="60" y="230" width="280" height="80" rx="12" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
  <text x="200" y="265" text-anchor="middle" fill="#1E3A8A" font-family="Arial,sans-serif" font-size="20" font-weight="bold">Coning \u0443 \u0412\u041d\u041a</text>
  <text x="200" y="292" text-anchor="middle" fill="#334155" font-family="Arial,sans-serif" font-size="16">matrix flow</text>
  <rect x="460" y="230" width="280" height="80" rx="12" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
  <text x="600" y="265" text-anchor="middle" fill="#1E3A8A" font-family="Arial,sans-serif" font-size="20" font-weight="bold">Channeling</text>
  <text x="600" y="292" text-anchor="middle" fill="#334155" font-family="Arial,sans-serif" font-size="16">\u0442\u0440\u0435\u0449\u0438\u043d\u0430 / wormhole</text>
  <rect x="860" y="230" width="280" height="80" rx="12" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
  <text x="1000" y="265" text-anchor="middle" fill="#1E3A8A" font-family="Arial,sans-serif" font-size="20" font-weight="bold">Cross-flow</text>
  <text x="1000" y="292" text-anchor="middle" fill="#334155" font-family="Arial,sans-serif" font-size="16">\u043c\u0435\u0436\u0434\u0443 \u043f\u0440\u043e\u043f\u043b\u0430\u0441\u0442\u043a\u0430\u043c\u0438</text>
  <rect x="60" y="360" width="280" height="90" rx="12" fill="#FEF3C7" stroke="#C8860A" stroke-width="2"/>
  <text x="200" y="415" text-anchor="middle" fill="#92400E" font-family="Arial,sans-serif" font-size="24" font-weight="bold">RPM</text>
  <rect x="460" y="360" width="280" height="90" rx="12" fill="#FEF3C7" stroke="#C8860A" stroke-width="2"/>
  <text x="600" y="415" text-anchor="middle" fill="#92400E" font-family="Arial,sans-serif" font-size="24" font-weight="bold">PPG / RPPG</text>
  <rect x="860" y="360" width="280" height="90" rx="12" fill="#FEF3C7" stroke="#C8860A" stroke-width="2"/>
  <text x="1000" y="415" text-anchor="middle" fill="#92400E" font-family="Arial,sans-serif" font-size="22" font-weight="bold">In-depth gel</text>
  <rect x="280" y="520" width="640" height="120" rx="16" fill="#FEE2E2" stroke="#DC2626" stroke-width="2"/>
  <text x="600" y="560" text-anchor="middle" fill="#991B1B" font-family="Arial,sans-serif" font-size="22" font-weight="bold">\u041d\u0415 \u041f\u041e\u0414\u0425\u041e\u0414\u0418\u0422</text>
  <text x="600" y="595" text-anchor="middle" fill="#334155" font-family="Arial,sans-serif" font-size="17">RPM \u043d\u0430 \u043e\u0442\u043a\u0440\u044b\u0442\u0443\u044e \u0442\u0440\u0435\u0449\u0438\u043d\u0443</text>
  <text x="600" y="620" text-anchor="middle" fill="#334155" font-family="Arial,sans-serif" font-size="17">\u00ab\u0423\u043d\u0438\u0432\u0435\u0440\u0441\u0430\u043b\u044c\u043d\u044b\u0439 \u0440\u0435\u0430\u0433\u0435\u043d\u0442\u00bb \u0431\u0435\u0437 core flood</text>
  <text x="600" y="690" text-anchor="middle" fill="#64748B" font-family="Arial,sans-serif" font-size="16">{L["dt_foot"]}</text>
</svg>'''


def svg04() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 680" width="1200" height="680">
  <rect width="1200" height="680" fill="#F8FAFC"/>
  <text x="600" y="55" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="34" font-weight="bold">{L["tri_t"]}</text>
  <text x="600" y="92" text-anchor="middle" fill="#64748B" font-family="Arial,sans-serif" font-size="20">{L["tri_s"]}</text>
  <rect x="40" y="130" width="350" height="500" rx="18" fill="#FFF" stroke="#2E86AB" stroke-width="3"/>
  <rect x="40" y="130" width="350" height="70" rx="18" fill="#2E86AB"/>
  <text x="215" y="175" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="28" font-weight="bold">RPM</text>
  <text x="215" y="240" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="17">\u0421\u043b\u043e\u0439 \u043d\u0430 \u0441\u0442\u0435\u043d\u043a\u0435 \u043f\u043e\u0440\u044b</text>
  <text x="70" y="310" fill="#16A34A" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["ok_r"]}</text>
  <text x="70" y="340" fill="#334155" font-family="Arial,sans-serif" font-size="15">coning, matrix flow</text>
  <text x="70" y="390" fill="#DC2626" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["no_r"]}</text>
  <text x="70" y="420" fill="#334155" font-family="Arial,sans-serif" font-size="15">\u043e\u0442\u043a\u0440\u044b\u0442\u044b\u0435 \u0442\u0440\u0435\u0449\u0438\u043d\u044b</text>
  <rect x="425" y="130" width="350" height="500" rx="18" fill="#FFF" stroke="#C8860A" stroke-width="3"/>
  <rect x="425" y="130" width="350" height="70" rx="18" fill="#C8860A"/>
  <text x="600" y="175" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{L["gel"]}</text>
  <text x="600" y="240" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="17">\u0416\u0438\u0434\u043a\u043e\u0435 \u2192 \u0442\u0432\u0451\u0440\u0434\u043e\u0435 \u0432 \u043f\u043b\u0430\u0441\u0442\u0435</text>
  <text x="455" y="310" fill="#16A34A" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["ok_r"]}</text>
  <text x="455" y="340" fill="#334155" font-family="Arial,sans-serif" font-size="15">HTHS, \u0441\u043b\u043e\u0436\u043d\u0430\u044f \u0433\u0435\u043e\u043b\u043e\u0433\u0438\u044f</text>
  <text x="455" y="390" fill="#DC2626" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["no_r"]}</text>
  <text x="455" y="420" fill="#334155" font-family="Arial,sans-serif" font-size="15">\u0431\u0435\u0437 \u0434\u0430\u043d\u043d\u044b\u0445 \u043f\u043e T \u043f\u043b\u0430\u0441\u0442\u0430</text>
  <rect x="810" y="130" width="350" height="500" rx="18" fill="#FFF" stroke="#7C3AED" stroke-width="3"/>
  <rect x="810" y="130" width="350" height="70" rx="18" fill="#7C3AED"/>
  <text x="985" y="175" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="28" font-weight="bold">RPPG</text>
  <text x="985" y="240" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="17">\u0427\u0430\u0441\u0442\u0438\u0446\u044b \u2192 \u043c\u043e\u043d\u043e\u043b\u0438\u0442\u043d\u0430\u044f \u043f\u0440\u043e\u0431\u043a\u0430</text>
  <text x="840" y="310" fill="#16A34A" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["ok_r"]}</text>
  <text x="840" y="340" fill="#334155" font-family="Arial,sans-serif" font-size="15">fracture, wormhole</text>
  <text x="840" y="390" fill="#DC2626" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{L["no_r"]}</text>
  <text x="840" y="420" fill="#334155" font-family="Arial,sans-serif" font-size="15">matrix coning \u0431\u0435\u0437 \u043a\u0430\u043d\u0430\u043b\u0430</text>
</svg>'''


def svg05() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 580" width="1200" height="580">
  <rect width="1200" height="580" fill="#0B1F3A"/>
  <text x="600" y="55" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="34" font-weight="bold">{L["hem_t"]}</text>
  <text x="600" y="92" text-anchor="middle" fill="#94A3B8" font-family="Arial,sans-serif" font-size="20">{L["hem_s"]}</text>
  <g font-family="Arial,sans-serif">
    <rect x="40" y="140" width="150" height="100" rx="12" fill="#1E3A5F" stroke="#5BC0EB" stroke-width="2"/>
    <text x="115" y="180" text-anchor="middle" fill="#5BC0EB" font-size="15" font-weight="bold">\u0411\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0430</text>
    <text x="210" y="195" fill="#64748B" font-size="28">\u2192</text>
    <rect x="230" y="140" width="150" height="100" rx="12" fill="#1E3A5F" stroke="#5BC0EB" stroke-width="2"/>
    <text x="305" y="180" text-anchor="middle" fill="#5BC0EB" font-size="15" font-weight="bold">ML / QSAR</text>
    <text x="400" y="195" fill="#64748B" font-size="28">\u2192</text>
    <rect x="420" y="140" width="150" height="100" rx="12" fill="#1E3A5F" stroke="#F4C542" stroke-width="2"/>
    <text x="495" y="180" text-anchor="middle" fill="#F4C542" font-size="15" font-weight="bold">Top-15</text>
    <text x="590" y="195" fill="#64748B" font-size="28">\u2192</text>
    <rect x="610" y="140" width="150" height="100" rx="12" fill="#1E3A5F" stroke="#16A34A" stroke-width="2"/>
    <text x="685" y="180" text-anchor="middle" fill="#4ADE80" font-size="15" font-weight="bold">Core flood</text>
    <text x="780" y="195" fill="#64748B" font-size="28">\u2192</text>
    <rect x="800" y="140" width="120" height="100" rx="12" fill="#16A34A"/>
    <text x="860" y="195" text-anchor="middle" fill="#FFF" font-size="15" font-weight="bold">DoE</text>
  </g>
  <text x="80" y="310" fill="#94A3B8" font-family="Arial,sans-serif" font-size="18">\u0411\u0435\u0437 \u0445\u0435\u043c\u043e\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0442\u0438\u043a\u0438</text>
  <rect x="80" y="325" width="900" height="36" rx="8" fill="#DC2626" opacity="0.9"/>
  <text x="990" y="349" fill="#FCA5A5" font-family="Arial,sans-serif" font-size="18" font-weight="bold">~100 \u043e\u043f\u044b\u0442\u043e\u0432</text>
  <text x="80" y="410" fill="#94A3B8" font-family="Arial,sans-serif" font-size="18">\u0421 \u0445\u0435\u043c\u043e\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0442\u0438\u043a\u043e\u0439</text>
  <rect x="80" y="425" width="900" height="36" rx="8" fill="#334155"/>
  <rect x="80" y="425" width="135" height="36" rx="8" fill="#16A34A"/>
  <text x="990" y="449" fill="#4ADE80" font-family="Arial,sans-serif" font-size="18" font-weight="bold">~15 \u043e\u043f\u044b\u0442\u043e\u0432</text>
  <text x="600" y="530" text-anchor="middle" fill="#F4C542" font-family="Arial,sans-serif" font-size="16" font-weight="bold">RPM \u00b7 \u0442\u0435\u0440\u043c\u043e\u0442\u0440\u043e\u043f\u043d\u044b\u0439 gel \u00b7 PPG</text>
</svg>'''


def svg06() -> str:
    items = [
        ("1", "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043c\u0435\u0445\u0430\u043d\u0438\u0437\u043c \u043e\u0431\u0432\u043e\u0434\u043d\u0435\u043d\u0438\u044f", "PLT \u00b7 tracers \u00b7 \u0438\u0441\u0442\u043e\u0440\u0438\u044f \u0434\u0435\u0431\u0438\u0442\u043e\u0432"),
        ("2", "\u041f\u043e\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441 \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0438", "RPM / gel / PPG \u2014 \u043f\u043e\u0434 \u043c\u0435\u0445\u0430\u043d\u0438\u0437\u043c"),
        ("3", "??? ????? ? ???????????", "Primary + backup (Track 1 + Track 2)"),
        ("4", "Gate \u043d\u0430 core flood", "Frrw/Frr\u043e \u043d\u0435 \u0441\u0445\u043e\u0434\u0438\u0442\u0441\u044f \u2192 \u0432 \u043f\u043e\u043b\u0435 \u043d\u0435 \u0438\u0434\u0451\u043c"),
        ("5", "\u0421\u0447\u0438\u0442\u0430\u0442\u044c \u044d\u043a\u043e\u043d\u043e\u043c\u0438\u043a\u0443", "\u20bd/\u0442 \u0432\u043e\u0434\u044b \u00b7 \u20bd/\u0442 \u043d\u0435\u0444\u0442\u0438"),
    ]
    rows = ""
    y = 130
    for num, title, sub in items:
        color = "#2E86AB" if int(num) <= 2 else "#16A34A" if int(num) >= 4 else "#C8860A"
        rows += f'''
  <rect x="80" y="{y}" width="1040" height="88" rx="14" fill="#FFF" stroke="#E2E8F0" stroke-width="2"/>
  <circle cx="130" cy="{y+44}" r="26" fill="{color}"/>
  <text x="130" y="{y+52}" text-anchor="middle" fill="#FFF" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{num}</text>
  <text x="180" y="{y+35}" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="21" font-weight="bold">{title}</text>
  <text x="180" y="{y+62}" fill="#64748B" font-family="Arial,sans-serif" font-size="16">{sub}</text>'''
        y += 103
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 720" width="1200" height="720">
  <rect width="1200" height="720" fill="#F8FAFC"/>
  <text x="600" y="55" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="34" font-weight="bold">{L["chk_t"]}</text>
  <text x="600" y="92" text-anchor="middle" fill="#64748B" font-family="Arial,sans-serif" font-size="20">{L["chk_s"]}</text>
  {rows}
</svg>'''


SLIDES = [
    ("01-oblozhka-linkedin", svg01, 1200, 644),
    ("02-uravnenie-uspeha", svg02, 1200, 675),
    ("03-vybor-tehnologii", svg03, 1200, 720),
    ("04-tri-tehnologii", svg04, 1200, 680),
    ("05-hemoinformatika", svg05, 1200, 580),
    ("06-cheklist-lidera", svg06, 1200, 720),
]


def write_svgs() -> list[tuple[str, str, int, int]]:
    written = []
    for stem, fn, w, h in SLIDES:
        svg_path = OUT / f"{stem}.svg"
        content = fn()
        svg_path.write_text(content, encoding="utf-8", newline="\n")
        written.append((stem, content, w, h))
        print("SVG", svg_path.name)
    return written


def export_jpg(slides: list[tuple[str, str, int, int]]) -> None:
    JPG_DIR.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for stem, content, w, h in slides:
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<style>*{margin:0;padding:0}body{background:#fff}</style></head>"
                f"<body>{content}</body></html>"
            )
            page.set_content(html, wait_until="networkidle")
            jpg_path = JPG_DIR / f"{stem}.jpg"
            page.screenshot(path=str(jpg_path), type="jpeg", quality=92)
            page.close()
            print("JPG", jpg_path.name)
        browser.close()


if __name__ == "__main__":
    slides = write_svgs()
    export_jpg(slides)
    manifest = [{"file": f"{s[0]}.jpg", "width": s[2], "height": s[3]} for s in slides]
    (JPG_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Done ->", JPG_DIR)
