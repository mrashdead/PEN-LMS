import { defineConfig } from 'vite';
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer';
import handlebars from 'vite-plugin-handlebars';
import { execSync } from 'child_process';
import { resolve } from 'path';
import copy from 'rollup-plugin-copy';
import path from 'path';
import { glob } from 'glob';

const folder = {
    src: "src/", // source files
    src_assets: "src/assets/", // source assets files
    dist: "dist/", // build files
    dist_assets: "dist/assets/" //build assets files
};

export default defineConfig(({ command }) => {
    const config = {
        plugins: [
            {
                name: 'preload-script',
                configResolved() {
                    // Run the preload script
                    execSync('node ./preload.js', { stdio: 'inherit' });
                    execSync('node ./rtlscss.js', { stdio: 'inherit' });
                }
            },
            handlebars({
                partialDirectory: resolve(__dirname, folder.src),
            }),
            ViteImageOptimizer({
                test: /\.(jpe?g|png|gif|tiff|webp|svg|avif)$/i,
                /* pass your config */
                svg: {
                    multipass: true,
                    ansiColors: true,
                    plugins: [
                        {
                            name: 'preset-default',
                            params: {
                                overrides: {
                                    cleanupNumericValues: false,
                                    removeViewBox: false, // https://github.com/svg/svgo/issues/1128
                                },
                                cleanupIDs: {
                                    minify: false,
                                    remove: false,
                                },
                                convertPathData: false,
                            },
                        },
                        'sortAttrs',
                        {
                            name: 'addAttributesToSVGElement',
                            params: {
                                attributes: [{ xmlns: 'http://www.w3.org/2000/svg' }],
                            },
                        },
                    ],
                },
                png: {
                    quality: 100,
                },
                jpeg: {
                    quality: 100,
                },
                jpg: {
                    quality: 100,
                },
                cache: false,
            }),
        ],
        base: '',
        // logLevel: 'error', // if you want to disable logging use 'info' | 'warn' | 'error' | 'silent'
        clearScreen: true,
        root: path.resolve(__dirname, folder.src),
        build: {
            outDir: '../dist',
            emptyOutDir: false,
            modulePreload: false,
            // watch: {},  // if you want to watch your build files
            rollupOptions: {
                manualChunks: undefined,
                input: {
                    icons: folder.src_assets + 'scss/icons.scss',
                    bootstrap: folder.src_assets + 'scss/bootstrap.scss',
                    app: folder.src_assets + 'scss/app.scss',
                    ...generateHtmlEntries(),
                },
                output: {
                    assetFileNames: (assetInfo) => {
                        const ext = assetInfo.name.split('.').pop();
                        if (ext === 'css') {
                            return 'assets/css/' + `[name]` + '.css';
                        } else if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
                            return 'assets/images/' + assetInfo.name;
                        } else {
                            return 'assets/css/' + assetInfo.name;
                        }
                    },
                    entryFileNames: 'assets/js/' + `[name]` + `.js`,
                },
                external: [
                    'jquery',
                    /^assets\/libs\//,
                    "@fullcalendar/core",
                    "@fullcalendar/resource-timeline",
                    "@fullcalendar/resource-day-grid",
                    "@fullcalendar/resource-time-grid",
                    "@fullcalendar/interaction",
                    "@fullcalendar/daygrid",
                    "@fullcalendar/timegrid",
                ],
                plugins: [
                    copy({
                        targets: [
                            { src: folder.src_assets + 'lang', dest: folder.dist_assets },
                            { src: folder.src_assets + 'json', dest: folder.dist_assets },
                            { src: folder.src_assets + 'js/table', dest: folder.dist_assets + 'js' },
                            { src: folder.src_assets + 'js/jalalidatepicker.min.js', dest: folder.dist_assets + 'js' },
                            { src: folder.src_assets + 'libs', dest: folder.dist_assets },
                            { src: folder.src_assets + 'images', dest: folder.dist_assets },
                            { src: 'src/assets/libs/lightbox2', dest: 'dist/assets/libs' },
                            { src: 'src/assets/fonts/Vazir', dest: 'dist/assets/fonts' }
                        ],
                    }),
                ],
            },
        },
        legacy: {
            buildSsrCjsExternalHeuristics: true
        },
        publicDir: 'dist',
        // TEMP: stabilize dev server on Windows (watcher / HMR pressure) by Spring Code
        server: {
            port: 8080,
            hot: true,
            hmr: {
                overlay: false
            },
            watch: {
                ignored: [
                    '**/node_modules/**',
                    '**/.git/**'
                ],
                usePolling: false
            }
        },
        css: {
            preprocessorOptions: {
                scss: {
                    silenceDeprecations: [
                        'import',
                        'mixed-decls',
                        'color-functions',
                        'global-builtin',
                    ],
                },
            },
        },
    }
    if (command === 'build') {
        config.plugins.push({
            name: 'admin-css-last',
            transformIndexHtml(html) {
                // Extract all CSS links
                const cssLinkRegex = /<link[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/g;
                const cssLinks = [];
                let match;

                // Collect all CSS links
                while ((match = cssLinkRegex.exec(html)) !== null) {
                    cssLinks.push({
                        full: match[0],
                        href: match[1],
                        // If it's admin.css, give it highest number to be last
                        priority: match[1].includes('admin.css') ? 999 : 1
                    });
                }

                // Remove all CSS links
                html = html.replace(cssLinkRegex, '');

                // Sort by priority (admin.css last)
                cssLinks.sort((a, b) => a.priority - b.priority);

                // Insert sorted CSS links before </head>
                const sortedLinks = cssLinks.map(link => link.full).join('\n  ');
                html = html.replace('</head>', `  ${sortedLinks}\n</head>`);

                return html;
            },
            enforce: 'post' // Run this after all other plugins
        })
    }
    return config;
})

function generateHtmlEntries() {
    const entries = {};

    // Modify the glob pattern to match your HTML file location
    const htmlFiles = glob.sync('src/*.html');
    htmlFiles.forEach((file) => {
        const name = file.replace('src/', '').replace('.html', '');
        entries[name] = file;
    });

    return entries;
}
