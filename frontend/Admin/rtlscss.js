import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import postcss from 'postcss';
import postcssImport from 'postcss-import';
import autoprefixer from 'autoprefixer';
import rtlcss from 'rtlcss';
import * as sass from 'sass';
import cssnano from 'cssnano';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const folder = {
    src: "src/", // source files
    src_assets: "src/assets/", // source assets files
    dist: "src/", // build files
    dist_assets: "assets/", //build assets files
    scss: {
        path: "src/assets/scss/",
        generatePath: "src/assets/css/",
        files: [
            'app.scss',
            'bootstrap.scss',
            'icons.scss',
        ]
    },
};

// Generate RTL CSS
generateAllCss().then(() => {
    console.log('All CSS generated successfully.');
}).catch(err => {
    console.error('Error during CSS generation:', err);
});

async function generateAllCss() {
    for (const file of folder.scss.files) {
        await generateRtlCss(file);
    }
}

async function generateRtlCss(scssFile) {
    const scssPath = path.resolve(__dirname, folder.scss.path, scssFile);
    const cssPath = path.resolve(__dirname, folder.scss.generatePath, scssFile);
    const rtlCssPath = path.resolve(__dirname, folder.scss.generatePath, scssFile.replace('.scss', '') + '.rtl.css');

    // Compile SCSS to CSS
    const { css: ltrCss } = await sass.compile(scssPath);

    // Generate RTL CSS
    const rtlResult = await postcss([
        postcssImport(),
        autoprefixer(),
    ]).process(ltrCss, { from: cssPath, to: rtlCssPath });

    const rtlCss = rtlcss.process(rtlResult, { autoRename: false, clean: false });
    fs.ensureDirSync(path.dirname(rtlCssPath)); // Ensure the directory exists
    fs.writeFileSync(rtlCssPath, rtlCss);
    // minify css with postcss
    const minifiedCss = await postcss([
        cssnano({
            preset: 'default',
        }),
    ]).process(rtlCss, { from: rtlCssPath, to: rtlCssPath });

    fs.ensureDirSync(path.dirname(cssPath)); // Ensure the directory exists
    fs.writeFileSync(rtlCssPath, minifiedCss.css);

}