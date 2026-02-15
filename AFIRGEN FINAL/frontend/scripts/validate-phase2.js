/**
 * Phase 2 Validation Script
 * 
 * This script validates that all Phase 2 (Performance Optimizations) tasks
 * are complete and meet the requirements.
 * 
 * Phase 2 Tasks:
 * - Task 9: API client with retry and caching
 * - Task 10: Minification and bundling
 * - Task 11: Service worker for offline capability
 * - Task 12: Optimize assets
 * - Task 13: Run performance tests
 * 
 * Usage:
 *   node scripts/validate-phase2.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(`  ${title}`, 'cyan');
  console.log('='.repeat(60) + '\n');
}

function checkFile(filePath, description) {
  const exists = fs.existsSync(filePath);
  const icon = exists ? '✅' : '❌';
  log(`  ${icon} ${description}: ${filePath}`, exists ? 'green' : 'red');
  return exists;
}

function checkDirectory(dirPath, description) {
  const exists = fs.existsSync(dirPath);
  const icon = exists ? '✅' : '❌';
  log(`  ${icon} ${description}: ${dirPath}`, exists ? 'green' : 'red');
  return exists;
}

function runCommand(command, description) {
  try {
    log(`  ⏳ Running: ${description}...`, 'yellow');
    const output = execSync(command, { encoding: 'utf-8', stdio: 'pipe' });
    log(`  ✅ ${description} - PASSED`, 'green');
    return { passed: true, output };
  } catch (error) {
    log(`  ❌ ${description} - FAILED`, 'red');
    if (error.stdout) {
      console.log(error.stdout);
    }
    if (error.stderr) {
      console.error(error.stderr);
    }
    return { passed: false, error: error.message };
  }
}

/**
 * Task 9: API client with retry and caching
 */
function validateTask9() {
  logSection('Task 9: API Client with Retry and Caching');
  
  let allPassed = true;
  
  // Check if api.js exists
  allPassed &= checkFile('js/api.js', 'API client module');
  
  // Check if api.js contains required functions
  if (fs.existsSync('js/api.js')) {
    const apiContent = fs.readFileSync('js/api.js', 'utf-8');
    
    const checks = [
      { pattern: /class\s+APIClient/, desc: 'APIClient class' },
      { pattern: /retryRequest|retry/, desc: 'Retry logic' },
      { pattern: /cache|Cache/, desc: 'Caching mechanism' },
      { pattern: /exponential|backoff/, desc: 'Exponential backoff' }
    ];
    
    checks.forEach(check => {
      const found = check.pattern.test(apiContent);
      const icon = found ? '✅' : '❌';
      log(`  ${icon} ${check.desc} implemented`, found ? 'green' : 'red');
      allPassed &= found;
    });
  }
  
  // Check for API tests
  const testFiles = ['js/api.test.js', 'js/__tests__/api.test.js'];
  const hasTests = testFiles.some(f => fs.existsSync(f));
  const icon = hasTests ? '✅' : '⚠️';
  log(`  ${icon} API tests exist`, hasTests ? 'green' : 'yellow');
  
  return allPassed;
}

/**
 * Task 10: Minification and bundling
 */
function validateTask10() {
  logSection('Task 10: Minification and Bundling');
  
  let allPassed = true;
  
  // Check build scripts in package.json
  if (fs.existsSync('package.json')) {
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
    
    const requiredScripts = [
      'build',
      'build:css',
      'build:js',
      'build:html'
    ];
    
    requiredScripts.forEach(script => {
      const exists = pkg.scripts && pkg.scripts[script];
      const icon = exists ? '✅' : '❌';
      log(`  ${icon} npm script: ${script}`, exists ? 'green' : 'red');
      allPassed &= exists;
    });
  }
  
  // Check if dist directory exists
  allPassed &= checkDirectory('dist', 'Distribution directory');
  
  // Check minified files
  if (fs.existsSync('dist')) {
    const minifiedFiles = [
      'dist/css/main.min.css',
      'dist/js/app.min.js',
      'dist/index.html'
    ];
    
    minifiedFiles.forEach(file => {
      allPassed &= checkFile(file, `Minified file: ${path.basename(file)}`);
    });
  }
  
  // Check configuration files
  const configFiles = [
    { path: 'terser.config.json', desc: 'Terser config' },
    { path: 'cssnano.config.js', desc: 'cssnano config' },
    { path: '.htmlminifierrc.json', desc: 'HTML minifier config' }
  ];
  
  configFiles.forEach(config => {
    checkFile(config.path, config.desc);
  });
  
  return allPassed;
}

/**
 * Task 11: Service worker for offline capability
 */
function validateTask11() {
  logSection('Task 11: Service Worker for Offline Capability');
  
  let allPassed = true;
  
  // Check if service worker exists
  allPassed &= checkFile('sw.js', 'Service worker');
  allPassed &= checkFile('dist/sw.js', 'Service worker (dist)');
  
  // Check service worker content
  if (fs.existsSync('sw.js')) {
    const swContent = fs.readFileSync('sw.js', 'utf-8');
    
    const checks = [
      { pattern: /install/, desc: 'Install event handler' },
      { pattern: /activate/, desc: 'Activate event handler' },
      { pattern: /fetch/, desc: 'Fetch event handler' },
      { pattern: /cache|Cache/, desc: 'Caching logic' },
      { pattern: /CACHE_NAME|cacheName/, desc: 'Cache naming' }
    ];
    
    checks.forEach(check => {
      const found = check.pattern.test(swContent);
      const icon = found ? '✅' : '❌';
      log(`  ${icon} ${check.desc}`, found ? 'green' : 'red');
      allPassed &= found;
    });
  }
  
  // Check if service worker is registered in app.js
  if (fs.existsSync('js/app.js')) {
    const appContent = fs.readFileSync('js/app.js', 'utf-8');
    const registered = /serviceWorker\.register|navigator\.serviceWorker/.test(appContent);
    const icon = registered ? '✅' : '❌';
    log(`  ${icon} Service worker registration in app.js`, registered ? 'green' : 'red');
    allPassed &= registered;
  }
  
  // Check offline page
  allPassed &= checkFile('offline.html', 'Offline fallback page');
  allPassed &= checkFile('dist/offline.html', 'Offline page (dist)');
  
  return allPassed;
}

/**
 * Task 12: Optimize assets
 */
function validateTask12() {
  logSection('Task 12: Optimize Assets');
  
  let allPassed = true;
  
  // Check for resource hints in index.html
  if (fs.existsSync('index.html')) {
    const htmlContent = fs.readFileSync('index.html', 'utf-8');
    
    const checks = [
      { pattern: /rel="preconnect"/, desc: 'Preconnect resource hint' },
      { pattern: /rel="dns-prefetch"/, desc: 'DNS-prefetch resource hint' },
      { pattern: /display=swap/, desc: 'Font display swap' }
    ];
    
    checks.forEach(check => {
      const found = check.pattern.test(htmlContent);
      const icon = found ? '✅' : '❌';
      log(`  ${icon} ${check.desc}`, found ? 'green' : 'red');
      allPassed &= found;
    });
  }
  
  // Check for asset optimization documentation
  checkFile('docs/ASSET-OPTIMIZATION-GUIDE.md', 'Asset optimization guide');
  
  return allPassed;
}

/**
 * Task 13: Run performance tests
 */
function validateTask13() {
  logSection('Task 13: Run Performance Tests');
  
  let allPassed = true;
  
  // Check performance testing scripts
  allPassed &= checkFile('scripts/performance-test.js', 'Performance test script');
  allPassed &= checkFile('scripts/check-bundle-sizes.js', 'Bundle size check script');
  
  // Check Lighthouse CI config
  allPassed &= checkFile('lighthouserc.json', 'Lighthouse CI config');
  
  // Check performance testing documentation
  allPassed &= checkFile('docs/PERFORMANCE-TESTING-GUIDE.md', 'Performance testing guide');
  allPassed &= checkFile('docs/PERFORMANCE-TESTING-QUICK-START.md', 'Performance quick start');
  
  // Check npm scripts
  if (fs.existsSync('package.json')) {
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
    
    const requiredScripts = [
      'test:performance',
      'test:bundle-size',
      'test:lighthouse'
    ];
    
    requiredScripts.forEach(script => {
      const exists = pkg.scripts && pkg.scripts[script];
      const icon = exists ? '✅' : '❌';
      log(`  ${icon} npm script: ${script}`, exists ? 'green' : 'red');
      allPassed &= exists;
    });
  }
  
  return allPassed;
}

/**
 * Run bundle size check
 */
function runBundleSizeCheck() {
  logSection('Bundle Size Verification');
  
  if (!fs.existsSync('dist')) {
    log('  ⚠️  dist/ directory not found. Run "npm run build" first.', 'yellow');
    return false;
  }
  
  const result = runCommand('node scripts/check-bundle-sizes.js', 'Bundle size check');
  return result.passed;
}

/**
 * Run unit tests
 */
function runUnitTests() {
  logSection('Unit Tests');
  
  const result = runCommand('npm test -- --passWithNoTests', 'Unit tests');
  return result.passed;
}

/**
 * Run ESLint
 */
function runLint() {
  logSection('ESLint');
  
  const result = runCommand('npm run lint', 'ESLint check');
  return result.passed;
}

/**
 * Check offline mode
 */
function checkOfflineMode() {
  logSection('Offline Mode');
  
  let allPassed = true;
  
  // Check service worker
  allPassed &= checkFile('sw.js', 'Service worker');
  
  // Check offline page
  allPassed &= checkFile('offline.html', 'Offline page');
  
  // Check if offline mode test exists
  const offlineTestFiles = [
    'js/offline-mode.pbt.test.js',
    'js/__tests__/offline-mode.test.js'
  ];
  
  const hasOfflineTest = offlineTestFiles.some(f => fs.existsSync(f));
  const icon = hasOfflineTest ? '✅' : '⚠️';
  log(`  ${icon} Offline mode tests`, hasOfflineTest ? 'green' : 'yellow');
  
  return allPassed;
}

/**
 * Main validation function
 */
function main() {
  console.log('\n');
  log('╔════════════════════════════════════════════════════════════╗', 'cyan');
  log('║         PHASE 2 VALIDATION - PERFORMANCE OPTIMIZATIONS     ║', 'cyan');
  log('╚════════════════════════════════════════════════════════════╝', 'cyan');
  
  const results = {
    task9: validateTask9(),
    task10: validateTask10(),
    task11: validateTask11(),
    task12: validateTask12(),
    task13: validateTask13(),
    bundleSize: runBundleSizeCheck(),
    unitTests: runUnitTests(),
    lint: runLint(),
    offlineMode: checkOfflineMode()
  };
  
  // Summary
  logSection('VALIDATION SUMMARY');
  
  const checks = [
    { name: 'Task 9: API Client', passed: results.task9 },
    { name: 'Task 10: Minification', passed: results.task10 },
    { name: 'Task 11: Service Worker', passed: results.task11 },
    { name: 'Task 12: Asset Optimization', passed: results.task12 },
    { name: 'Task 13: Performance Tests', passed: results.task13 },
    { name: 'Bundle Size Check', passed: results.bundleSize },
    { name: 'Unit Tests', passed: results.unitTests },
    { name: 'ESLint', passed: results.lint },
    { name: 'Offline Mode', passed: results.offlineMode }
  ];
  
  checks.forEach(check => {
    const icon = check.passed ? '✅' : '❌';
    const color = check.passed ? 'green' : 'red';
    log(`  ${icon} ${check.name}`, color);
  });
  
  const allPassed = Object.values(results).every(r => r);
  
  console.log('\n' + '='.repeat(60));
  if (allPassed) {
    log('  ✅ PHASE 2 VALIDATION PASSED', 'green');
    log('  All performance optimization tasks are complete!', 'green');
  } else {
    log('  ❌ PHASE 2 VALIDATION FAILED', 'red');
    log('  Some tasks need attention. Review the output above.', 'yellow');
  }
  console.log('='.repeat(60) + '\n');
  
  // Next steps
  if (allPassed) {
    log('Next Steps:', 'cyan');
    log('  1. Review Lighthouse reports in performance-reports/', 'blue');
    log('  2. Test offline mode in browser DevTools', 'blue');
    log('  3. Verify service worker in Application tab', 'blue');
    log('  4. Proceed to Phase 3: New Features', 'blue');
  } else {
    log('Action Items:', 'cyan');
    log('  1. Review failed checks above', 'yellow');
    log('  2. Complete missing tasks', 'yellow');
    log('  3. Run validation again', 'yellow');
  }
  
  console.log('');
  
  process.exit(allPassed ? 0 : 1);
}

// Run validation
if (require.main === module) {
  main();
}

module.exports = {
  validateTask9,
  validateTask10,
  validateTask11,
  validateTask12,
  validateTask13
};
