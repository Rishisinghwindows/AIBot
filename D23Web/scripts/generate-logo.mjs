import sharp from 'sharp';
import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, '..', 'public');

// D23 Logo SVG (512x512)
const logoSvg = `
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#8B5CF6"/>
      <stop offset="50%" style="stop-color:#D946EF"/>
      <stop offset="100%" style="stop-color:#EC4899"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="80" fill="url(#grad)"/>
  <text x="256" y="320" font-family="Arial, sans-serif" font-size="220" font-weight="bold" fill="white" text-anchor="middle">D23</text>
</svg>
`;

// OG Image SVG (1200x630)
const ogSvg = `
<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e"/>
      <stop offset="100%" style="stop-color:#0a0a0a"/>
    </linearGradient>
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#8B5CF6"/>
      <stop offset="50%" style="stop-color:#D946EF"/>
      <stop offset="100%" style="stop-color:#EC4899"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bgGrad)"/>
  <circle cx="100" cy="100" r="300" fill="#8B5CF6" fill-opacity="0.15"/>
  <circle cx="1100" cy="530" r="350" fill="#EC4899" fill-opacity="0.1"/>
  <text x="600" y="260" font-family="Arial, sans-serif" font-size="160" font-weight="bold" fill="white" text-anchor="middle">D23</text>
  <text x="600" y="260" font-family="Arial, sans-serif" font-size="160" font-weight="bold" fill="url(#textGrad)" text-anchor="middle" dx="250">.AI</text>
  <text x="600" y="360" font-family="Arial, sans-serif" font-size="36" fill="#a1a1aa" text-anchor="middle">Bharat's First WhatsApp AI Assistant</text>
  <text x="600" y="420" font-family="Arial, sans-serif" font-size="24" fill="#71717a" text-anchor="middle">11+ Indian Languages | Voice | Images | Games</text>
</svg>
`;

async function generateImages() {
  try {
    // Generate logo.png (512x512)
    await sharp(Buffer.from(logoSvg))
      .resize(512, 512)
      .png()
      .toFile(join(publicDir, 'puch', 'logo.png'));
    console.log('Created: puch/logo.png');

    // Generate d23-logo.png (512x512)
    await sharp(Buffer.from(logoSvg))
      .resize(512, 512)
      .png()
      .toFile(join(publicDir, 'd23-logo.png'));
    console.log('Created: d23-logo.png');

    // Generate apple-icon.png (180x180)
    await sharp(Buffer.from(logoSvg))
      .resize(180, 180)
      .png()
      .toFile(join(publicDir, 'apple-icon.png'));
    console.log('Created: apple-icon.png');

    // Generate OG image (1200x630)
    await sharp(Buffer.from(ogSvg))
      .resize(1200, 630)
      .png()
      .toFile(join(publicDir, 'd23-og.png'));
    console.log('Created: d23-og.png');

    console.log('\nAll images generated successfully!');
  } catch (error) {
    console.error('Error generating images:', error);
  }
}

generateImages();
