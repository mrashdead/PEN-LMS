import { cp, mkdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const config = JSON.parse(await readFile('package-libs-config.json', 'utf8'));
for (const packageName of config.packagesToCopy) {
    const destination = resolve('src/assets/libs', packageName);
    await mkdir(destination, { recursive: true });
    await cp(resolve('node_modules', packageName), destination, { recursive: true });
}
