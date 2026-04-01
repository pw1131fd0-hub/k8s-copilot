// Verify i18n translation completeness across all languages
const fs = require('fs');
const path = require('path');

const localesDir = 'frontend/src/i18n/locales';

// Read all language files
const languages = ['en.json', 'zh.json', 'zh-TW.json', 'ja.json'];
const translations = {};
const allKeys = new Set();

languages.forEach(lang => {
  const filePath = path.join(localesDir, lang);
  const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  translations[lang] = content;
  
  // Collect all keys
  function collectKeys(obj, prefix = '') {
    Object.keys(obj).forEach(key => {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      if (typeof obj[key] === 'object') {
        collectKeys(obj[key], fullKey);
      } else {
        allKeys.add(fullKey);
      }
    });
  }
  collectKeys(content);
});

console.log('\n=== i18n Completeness Report ===\n');
console.log(`Total unique translation keys: ${allKeys.size}`);
console.log('\nLanguage Coverage:');

languages.forEach(lang => {
  const content = translations[lang];
  let count = 0;
  
  function countKeys(obj) {
    Object.keys(obj).forEach(key => {
      if (typeof obj[key] === 'object') {
        countKeys(obj[key]);
      } else {
        count++;
      }
    });
  }
  countKeys(content);
  
  const coverage = ((count / allKeys.size) * 100).toFixed(1);
  console.log(`  - ${lang.padEnd(10)}: ${count} keys (${coverage}% coverage)`);
});

// Check for missing translations
console.log('\nMissing Translations Check:');
let missingFound = false;

languages.forEach(lang => {
  const content = translations[lang];
  const missing = [];
  
  allKeys.forEach(key => {
    const parts = key.split('.');
    let obj = content;
    let found = true;
    
    for (let part of parts) {
      if (obj && typeof obj === 'object' && part in obj) {
        obj = obj[part];
      } else {
        found = false;
        break;
      }
    }
    
    if (!found) {
      missing.push(key);
    }
  });
  
  if (missing.length > 0) {
    missingFound = true;
    console.log(`  ${lang}: ${missing.length} missing`);
    if (missing.length <= 5) {
      missing.forEach(key => console.log(`    - ${key}`));
    }
  } else {
    console.log(`  ${lang}: ✅ Complete`);
  }
});

console.log('\n=== Report Complete ===\n');
