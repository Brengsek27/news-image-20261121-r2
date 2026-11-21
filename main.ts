import * as fs from 'node:fs';
import * as path from 'node:path';

function validateAndCopy() {
    const entryPath = new URL('./entry.png', import.meta.url);
    const filePath = entryPath.pathname;

    if (!fs.existsSync(filePath)) {
        console.error(`Error: entry.png not found at ${filePath}`);
        process.exit(1);
    }

    const stats = fs.statSync(filePath);
    if (stats.size > 1048576) {
        console.error(`Error: entry.png size (${stats.size} bytes) exceeds 1,048,576 bytes limit.`);
        process.exit(1);
    }

    const fd = fs.openSync(filePath, 'r');
    const header = Buffer.alloc(24);
    fs.readSync(fd, header, 0, 24, 0);
    fs.closeSync(fd);

    const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
    if (!header.subarray(0, 8).equals(pngSignature)) {
        console.error('Error: entry.png does not have a valid PNG signature.');
        process.exit(1);
    }

    if (header.toString('ascii', 12, 16) !== 'IHDR') {
        console.error('Error: entry.png missing IHDR chunk.');
        process.exit(1);
    }

    const width = header.readUInt32BE(16);
    const height = header.readUInt32BE(20);

    if (width !== 1024 || height !== 1024) {
        console.error(`Error: entry.png dimensions are ${width}x${height}, expected exactly 1024x1024.`);
        process.exit(1);
    }

    const outputDir = process.env.MAKEFUN_OUTPUT_DIR || '/output';
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const destPath = path.join(outputDir, 'entry.png');
    fs.copyFileSync(filePath, destPath);
    console.log(`Successfully validated and copied entry.png to ${destPath}`);
}

validateAndCopy();
