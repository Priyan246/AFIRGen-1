/**
 * Bundle Size Verification Script
 * 
 * This script checks if the bundle sizes meet the requirements:
 * - main.css: <50KB (gzipped)
 * - app.js: <100KB (gzipped)
 * - vendor.js: <150KB (gzipped)
 * - Total: <500KB (gzipped)
 * 
 * Usage:
 *   node scripts/check-bundle-sizes.js
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// Thresholds (in KB)
const THRESHOLDS = {
  css: 50,
  appJs: 100,
  vendorJs: 150,
  total: 500
};

/**
 * Get gzipped size of a file
 */
function getGzippedSize(filePath) {
  if (!fs.existsSync(filePath)) {
    return 0;
  }
  
  const content = fs.readFileSync(filePath);
  const gzipped = zlib.gzipSync(content, { level: 9 });
  return gzipped.length;
}

/**
 * Get size of all files in a directory matching extension
 */
function getDirectorySize(dir, ext) {
  if (!fs.existsSync(dir)) {
    return 0;
  }

  let total = 0;
  
  function walk(directory) {
    const files = fs.readdirSync(directory);
    
    files.forEach(file => {
      const filePath = path.join(directory, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        walk(filePath);
      } else if (filePath.endsWith(ext)) {
        total += getGzippedSize(filePath);
      }
    });
  }
  
  walk(dir);
  return total;
}

/**
 * Format bytes to KB
 */
function formatKB(bytes) {
  return (bytes / 1024).toFixed(2);
}

/**
 * Main function
 */
function main() {
  console.log('\n📦 Bundle Size Verification\n');
  console.log('='.repeat(60) + '\n');

  const distDir = path.join(__dirname, '..', 'dist');
  
  if (!fs.existsSync(distDir)) {
    console.error('❌ Error: dist/ directory not found');
    console.error('   Please run "npm run build" first\n');
    process.exit(1);
  }

  // Calculate sizes
  const cssSize = getDirectorySize(path.join(distDir, 'css'), '.css');
  const jsSize = getDirectorySize(path.join(distDir, 'js'), '.js');
  const libSize = getDirectorySize(path.join(distDir, 'lib'), '.js');
  const htmlSize = getDirectorySize(distDir, '.html');
  
  const totalSize = cssSize + jsSize + libSize + htmlSize;

  // Print results
  console.log('📊 BUNDLE SIZES (gzipped):\n');
  
  const results = [
    {
      name: 'CSS',
      size: cssSize,
      threshold: THRESHOLDS.css * 1024,
      category: 'css'
    },
    {
      name: 'App JS',
      size: jsSize,
      threshold: THRESHOLDS.appJs * 1024,
      category: 'appJs'
    },
    {
      name: 'Lib JS (vendor)',
      size: libSize,
      threshold: THRESHOLDS.vendorJs * 1024,
      category: 'vendorJs'
    },
    {
      name: 'HTML',
      size: htmlSize,
      threshold: null,
      category: 'html'
    },
    {
      name: 'TOTAL',
      size: totalSize,
      threshold: THRESHOLDS.total * 1024,
      category: 'total'
    }
  ];

  let allPassed = true;

  results.forEach(result => {
    const sizeKB = formatKB(result.size);
    const icon = result.threshold && result.size > result.threshold ? '❌' : '✅';
    
    if (result.threshold) {
      const thresholdKB = formatKB(result.threshold);
      const percentage = ((result.size / result.threshold) * 100).toFixed(1);
      console.log(`  ${icon} ${result.name.padEnd(20)} ${sizeKB.padStart(8)} KB / ${thresholdKB} KB (${percentage}%)`);
      
      if (result.size > result.threshold) {
        allPassed = false;
      }
    } else {
      console.log(`  ℹ️  ${result.name.padEnd(20)} ${sizeKB.padStart(8)} KB`);
    }
  });

  console.log('\n' + '='.repeat(60) + '\n');

  // Detailed breakdown
  console.log('📋 DETAILED BREAKDOWN:\n');
  
  // CSS files
  const cssDir = path.join(distDir, 'css');
  if (fs.existsSync(cssDir)) {
    console.log('  CSS Files:');
    fs.readdirSync(cssDir).forEach(file => {
      if (file.endsWith('.css')) {
        const filePath = path.join(cssDir, file);
        const size = getGzippedSize(filePath);
        console.log(`    - ${file.padEnd(30)} ${formatKB(size).padStart(8)} KB`);
      }
    });
    console.log('');
  }

  // JS files
  const jsDir = path.join(distDir, 'js');
  if (fs.existsSync(jsDir)) {
    console.log('  JS Files:');
    fs.readdirSync(jsDir).forEach(file => {
      if (file.endsWith('.js')) {
        const filePath = path.join(jsDir, file);
        const size = getGzippedSize(filePath);
        console.log(`    - ${file.padEnd(30)} ${formatKB(size).padStart(8)} KB`);
      }
    });
    console.log('');
  }

  // Lib files
  const libDir = path.join(distDir, 'lib');
  if (fs.existsSync(libDir)) {
    console.log('  Library Files:');
    fs.readdirSync(libDir).forEach(file => {
      if (file.endsWith('.js')) {
        const filePath = path.join(libDir, file);
        const size = getGzippedSize(filePath);
        console.log(`    - ${file.padEnd(30)} ${formatKB(size).padStart(8)} KB`);
      }
    });
    console.log('');
  }

  console.log('='.repeat(60) + '\n');

  // Final result
  if (allPassed) {
    console.log('✅ ALL BUNDLE SIZE CHECKS PASSED\n');
    process.exit(0);
  } else {
    console.log('❌ SOME BUNDLE SIZE CHECKS FAILED\n');
    console.log('Recommendations:');
    console.log('  - Enable code splitting');
    console.log('  - Remove unused dependencies');
    console.log('  - Use tree shaking');
    console.log('  - Lazy load non-critical code');
    console.log('  - Consider using a CDN for large libraries\n');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { getGzippedSize, getDirectorySize };
