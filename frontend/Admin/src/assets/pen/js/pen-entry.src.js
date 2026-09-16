/*
 * Pen LMS entry — compiled with Vite (vite.pen.config.js), NOT served raw.
 * Mirrors the theme's admin.bundle.js core (Bootstrap 5 + SimpleBar + Lucide)
 * and additionally exposes window.lucide / window.penRenderIcons so the
 * dynamic UI (forms.js error rows, attachments) can re-hydrate icons after
 * injecting <i data-lucide> nodes at runtime.
 */
import 'simplebar';
import 'simplebar/dist/simplebar.css';
import * as bootstrap from 'bootstrap';
import { createIcons, icons } from 'lucide';

window.bootstrap = bootstrap;
window.lucide = { createIcons, icons };
window.penRenderIcons = function () { createIcons({ icons }); };

document.addEventListener('DOMContentLoaded', function () { createIcons({ icons }); });
window.addEventListener('load', function () { setTimeout(function () { createIcons({ icons }); }, 0); });
