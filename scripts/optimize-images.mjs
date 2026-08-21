import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import { readdir, unlink } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const docs = path.join(root, "docs");
const imagesDir = path.join(docs, "assets", "images");

async function loadSharp() {
  try {
    return (await import("sharp")).default;
  } catch {
    const require = createRequire(import.meta.url);
    const localSharp = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp";
    if (existsSync(localSharp)) {
      return require(localSharp);
    }
    throw new Error("sharp is required. Run npm install before optimizing images.");
  }
}

async function listPngFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await listPngFiles(fullPath));
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".png")) {
      files.push(fullPath);
    }
  }
  return files;
}

const sharp = await loadSharp();
const pngFiles = await listPngFiles(imagesDir);

for (const pngPath of pngFiles) {
  const webpPath = pngPath.replace(/\.png$/i, ".webp");
  const pipeline = sharp(pngPath);
  if (path.basename(pngPath).toLowerCase() === "codigo-error-hero-v2.png") {
    pipeline.resize({ width: 1440, height: 810, fit: "cover", position: "centre" });
  }
  await pipeline
    .webp({ quality: 74, effort: 5 })
    .toFile(webpPath);
  await unlink(pngPath);
}

console.log(`Optimized ${pngFiles.length} images to WebP.`);
