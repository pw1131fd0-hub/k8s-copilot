// Verify i18n content in production build
const fs = require('fs');
const path = require('path');

const buildDir = 'frontend/build';
const jsFile = 'frontend/build/static/js/main.f3718afb.js';

if (!fs.existsSync(jsFile)) {
  console.log('❌ Build file not found');
  process.exit(1);
}

const content = fs.readFileSync(jsFile, 'utf8');

console.log('\n=== Build i18n Verification ===\n');

// Check for language keys in build
const languages = ['en', 'zh', 'zh-TW', 'ja'];
const keysToCheck = [
  'appName',
  'ClawBook',
  '爪之書',
  'フィード',
  'トレンド',
  '決定パス'
];

console.log('Checking for language content in build:');

let foundKeys = 0;
keysToCheck.forEach(key => {
  if (content.includes(key)) {
    console.log(`  ✅ Found: "${key}"`);
    foundKeys++;
  } else {
    console.log(`  ⚠️  Missing: "${key}"`);
  }
});

// Check file size
const stats = fs.statSync(jsFile);
const gzipSize = (stats.size / 1024).toFixed(2);

console.log(`\nBuild File Size: ${gzipSize} KB (reported: 88.03 KB gzipped)`);
console.log(`Keys Found: ${foundKeys}/${keysToCheck.length}`);
console.log('\n=== Verification Complete ===\n');
