# -*- coding: utf-8 -*-
"""Rebuild all SVG infographics with UTF-8 + XML declaration."""
from pathlib import Path

OUT = Path(__file__).parent

SVG = [
("01-oblozhka-linkedin.svg", '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 644" width="1200" height="644">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B1F3A"/>
      <stop offset="55%" stop-color="#123456"/>
      <stop offset="100%" stop-color="#1A4D6E"/>
    </linearGradient>
    <linearGradient id="oil" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#F4C542"/>
      <stop offset="100%" stop-color="#C8860A"/>
    </linearGradient>
    <linearGradient id="water" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#5BC0EB"/>
      <stop offset="100%" stop-color="#2E86AB"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="644" fill="url(#bg)"/>
  <circle cx="980" cy="120" r="180" fill="#ffffff" opacity="0.04"/>
  <circle cx="1050" cy="520" r="240" fill="#ffffff" opacity="0.03"/>
  <g transform="translate(780, 90)">
    <rect x="70" y="0" width="36" height="420" fill="#334155" rx="4"/>
    <rect x="78" y="180" width="20" height="160" fill="url(#water)" opacity="0.9"/>
    <rect x="78" y="250" width="20" height="90" fill="url(#oil)" opacity="0.95"/>
    <path d="M88 420 L60 470 L116 470 Z" fill="#475569"/>
    <text x="88" y="505" text-anchor="middle" fill="#94A3B8" font-family="Arial,sans-serif" font-size="14">????????</text>
    <text x="130" y="230" fill="#5BC0EB" font-family="Arial,sans-serif" font-size="16" font-weight="bold">H2O</text>
    <text x="130" y="300" fill="#F4C542" font-family="Arial,sans-serif" font-size="16" font-weight="bold">oil</text>
  </g>
  <text x="80" y="120" fill="#FFFFFF" font-family="Arial,sans-serif" font-size="22" letter-spacing="2">??????????? &#183; ??????????? ???????????</text>
  <text x="80" y="210" fill="#FFFFFF" font-family="Arial,sans-serif" font-size="52" font-weight="bold">???? ?? ????.</text>
  <text x="80" y="275" fill="#F4C542" font-family="Arial,sans-serif" font-size="52" font-weight="bold">???? &#8212; ???????????? ????????.</text>
  <text x="80" y="340" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="24">??????????? ???: ??????????? + ????? + ????? ??????????</text>
  <g transform="translate(80, 390)">
    <rect width="210" height="56" rx="28" fill="#ffffff" opacity="0.12"/>
    <text x="24" y="35" fill="#FFFFFF" font-family="Arial,sans-serif" font-size="20" font-weight="bold">3000+</text>
    <text x="92" y="35" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="18">RPM-????????? ? ????</text>
  </g>
  <g transform="translate(320, 390)">
    <rect width="250" height="56" rx="28" fill="#ffffff" opacity="0.12"/>
    <text x="24" y="35" fill="#FFFFFF" font-family="Arial,sans-serif" font-size="20" font-weight="bold">85%</text>
    <text x="82" y="35" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="18">???????? ?????????????</text>
  </g>
  <g transform="translate(600, 390)">
    <rect width="280" height="56" rx="28" fill="#E8A838" opacity="0.95"/>
    <text x="24" y="35" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="18" font-weight="bold">#1 ?????? &#8212; candidate selection</text>
  </g>
  <text x="80" y="590" fill="#64748B" font-family="Arial,sans-serif" font-size="16">?????? ??? LinkedIn &#183; vodopritok project</text>
</svg>'''),

("02-uravnenie-uspeha.svg", '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="1200" height="675">
  <defs>
    <linearGradient id="blueG" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#E8F4FC"/>
      <stop offset="100%" stop-color="#D0E8F7"/>
    </linearGradient>
    <linearGradient id="goldG" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFF8E7"/>
      <stop offset="100%" stop-color="#FCECC5"/>
    </linearGradient>
    <linearGradient id="greenG" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#E8F8EE"/>
      <stop offset="100%" stop-color="#C8EDD6"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="675" fill="#F8FAFC"/>
  <text x="600" y="70" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="36" font-weight="bold">????????? ????????? ???</text>
  <text x="600" y="110" text-anchor="middle" fill="#64748B" font-family="Arial,sans-serif" font-size="20">?? &#171;????? ??????? ??????&#187;, ? &#171;??? ?????? ?????&#187;</text>
  <rect x="60" y="170" width="320" height="360" rx="20" fill="url(#blueG)" stroke="#2E86AB" stroke-width="3"/>
  <circle cx="220" cy="230" r="42" fill="#2E86AB"/>
  <text x="220" y="242" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="32" font-weight="bold">1</text>
  <text x="220" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="28" font-weight="bold">???????????</text>
  <text x="90" y="360" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; PLT / ????????????? ???????</text>
  <text x="90" y="395" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; ??????? ??????? ?????/????</text>
  <text x="90" y="430" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; Tracers, cross-flow</text>
  <text x="90" y="465" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; ????????: coning / channel /</text>
  <text x="90" y="490" fill="#334155" font-family="Arial,sans-serif" font-size="18">  cross-flow / behind-casing</text>
  <text x="430" y="370" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="72" font-weight="bold">+</text>
  <rect x="460" y="170" width="320" height="360" rx="20" fill="url(#goldG)" stroke="#C8860A" stroke-width="3"/>
  <circle cx="620" cy="230" r="42" fill="#C8860A"/>
  <text x="620" y="242" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="32" font-weight="bold">2</text>
  <text x="620" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="28" font-weight="bold">?????</text>
  <text x="490" y="360" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; RPM &#8212; ??????? ?????????????</text>
  <text x="490" y="395" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; ???? &#8212; ?????????? / ?????????</text>
  <text x="490" y="430" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; PPG/RPPG &#8212; ??????? ? ??????</text>
  <text x="490" y="465" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; ????????? ??? T, salinity, Ca&#178;&#8314;</text>
  <text x="490" y="500" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8226; Core flood gate ????? ?????</text>
  <text x="830" y="370" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="72" font-weight="bold">=</text>
  <rect x="860" y="170" width="280" height="360" rx="20" fill="url(#greenG)" stroke="#16A34A" stroke-width="3"/>
  <circle cx="1000" cy="230" r="42" fill="#16A34A"/>
  <text x="1000" y="248" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="28" font-weight="bold">OK</text>
  <text x="1000" y="310" text-anchor="middle" fill="#0B1F3A" font-family="Arial,sans-serif" font-size="26" font-weight="bold">??????</text>
  <text x="890" y="370" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8595; ?????????????</text>
  <text x="890" y="410" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8594; ??? ??????????</text>
  <text x="890" y="435" fill="#334155" font-family="Arial,sans-serif" font-size="18">  ?????? ?????</text>
  <text x="890" y="475" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8595; OPEX ???????</text>
  <text x="890" y="515" fill="#334155" font-family="Arial,sans-serif" font-size="18">&#8593; ???? ????? ????????</text>
  <rect x="120" y="570" width="960" height="70" rx="12" fill="#0B1F3A"/>
  <text x="600" y="615" text-anchor="middle" fill="#FFFFFF" font-family="Arial,sans-serif" font-size="22" font-weight="bold">????? &#8212; ???????? ?????????. ??????????? &#8212; ??????.</text>
</svg>'''),
]

# Continue in part 2 - file too long, append rest via second write or run multiple

if __name__ == "__main__":
    for name, content in SVG:
        (OUT / name).write_text(content, encoding="utf-8", newline="\n")
        print("OK", name)
