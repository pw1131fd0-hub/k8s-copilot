// Verify i18n integration in key components
const fs = require('fs');
const path = require('path');

const componentsToCheck = [
  'frontend/src/pages/Feed.js',
  'frontend/src/pages/Trends.js',
  'frontend/src/pages/DecisionPaths.js',
  'frontend/src/components/Sidebar.js',
  'frontend/src/components/Header.js',
  'frontend/src/components/PostCard.js',
  'frontend/src/components/PostComposer.js',
  'frontend/src/components/ExportModal.js'
];

console.log('\n=== i18n Integration Report ===\n');

let totalComponents = 0;
let integratedComponents = 0;

componentsToCheck.forEach(filePath => {
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  ${filePath} - NOT FOUND`);
    return;
  }
  
  totalComponents++;
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Check for useTranslation hook
  const hasUseTranslation = content.includes("useTranslation") || content.includes("useTranslation()");
  const hasT = content.includes("const { t }") || content.includes("const {t}");
  
  if (hasUseTranslation && hasT) {
    integratedComponents++;
    console.log(`✅ ${path.basename(filePath)}`);
    
    // Count t() calls
    const tCalls = (content.match(/t\(/g) || []).length;
    console.log(`   Uses: ${tCalls} translation keys`);
  } else {
    console.log(`❌ ${path.basename(filePath)} - Missing i18n integration`);
  }
});

console.log(`\nIntegration Status: ${integratedComponents}/${totalComponents} components`);
console.log(`Coverage: ${((integratedComponents/totalComponents)*100).toFixed(1)}%`);
console.log('\n=== Report Complete ===\n');
