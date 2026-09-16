// Pen LMS bundle build — compiles ONLY the small custom entry (no demo pages).
// Run from frontend/Admin:   npx vite build --config vite.pen.config.js
// Output: src/assets/pen/dist/pen.bundle.js  → served via {% static %}, no watch/build in the request path.
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    root: resolve(__dirname, 'src'),
    publicDir: false,
    build: {
        outDir: 'assets/pen/dist', // relative to root (src/) → src/assets/pen/dist
        emptyOutDir: true,
        modulePreload: false,
        rollupOptions: {
            input: {
                pen: resolve(__dirname, 'src/assets/pen/js/pen-entry.src.js'),
            },
            output: {
                entryFileNames: 'pen.bundle.js',
                assetFileNames: 'pen.bundle[extname]',
            },
        },
    },
});
