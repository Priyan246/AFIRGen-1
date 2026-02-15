/**
 * Automated Performance Testing Script
 * 
 * This script runs Lighthouse audits and checks if the application
 * meets the performance requirements specified in the design document.
 * 
 * Requirements:
 * - Performance score >90
 * - FCP <1s (1000ms)
 * - TTI <3s (3000ms)
 * - Bundle size <500KB (gzipped)
 * 
 * Usage:
 *   node scripts/performance-test.js [url]
 * 
 * Example:
 *   node scripts/performance-test.js http://localhost:3000
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

// Configuration
const TARGET_URL = process.argv[2] || 'http://localhost:3000';
const OUTPUT_DIR = path.join(__dirname, '..', 'performance-reports');
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-');

// Performance thresholds
const THRESHOLDS = {
  performanceScore: 90,
  accessibilityScore: 90,
  firstContentfulPaint: 1000, // ms
  timeToInteractive: 3000, // ms
  speedIndex: 2000, // ms
  totalBlockingTime: 300, // ms
  cumulativeLayoutShift: 0.1,
  largestContentfulPaint: 2500 // ms
};

/**
 * Run Lighthouse audit
 */
async function runLighthouse(url, device = 'desktop') {
  console.log(`\n🚀 Running Lighthouse audit for ${device}...`);
  console.log(`URL: ${url}\n`);

  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu']
  });

  const options = {
    logLevel: 'error',
    output: ['html', 'json'],
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    port: chrome.port,
    formFactor: device,
    screenEmulation: device === 'mobile' ? {
      mobile: true,
      width: 375,
      height: 667,
      deviceScaleFactor: 2,
      disabled: false
    } : {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false
    }
  };

  try {
    const runnerResult = await lighthouse(url, options);
    await chrome.kill();
    return runnerResult;
  } catch (error) {
    await chrome.kill();
    throw error;
  }
}

/**
 * Extract and format metrics
 */
function extractMetrics(lhr) {
  const categories = lhr.categories;
  const audits = lhr.audits;
  const metrics = audits.metrics?.details?.items?.[0] || {};

  return {
    scores: {
      performance: Math.round(categories.performance.score * 100),
      accessibility: Math.round(categories.accessibility.score * 100),
      bestPractices: Math.round(categories['best-practices'].score * 100),
      seo: Math.round(categories.seo.score * 100)
    },
    metrics: {
      firstContentfulPaint: metrics.firstContentfulPaint || 0,
      speedIndex: metrics.speedIndex || 0,
      largestContentfulPaint: metrics.largestContentfulPaint || 0,
      timeToInteractive: metrics.interactive || 0,
      totalBlockingTime: metrics.totalBlockingTime || 0,
      cumulativeLayoutShift: metrics.cumulativeLayoutShift || 0
    },
    diagnostics: {
      mainThreadWork: audits['mainthread-work-breakdown']?.numericValue || 0,
      bootupTime: audits['bootup-time']?.numericValue || 0,
      networkRequests: audits['network-requests']?.details?.items?.length || 0,
      totalByteWeight: audits['total-byte-weight']?.numericValue || 0
    }
  };
}

/**
 * Check if metrics meet thresholds
 */
function checkThresholds(results) {
  const { scores, metrics } = results;
  const checks = [];

  // Score checks
  checks.push({
    name: 'Performance Score',
    value: scores.performance,
    threshold: THRESHOLDS.performanceScore,
    unit: '',
    passed: scores.performance >= THRESHOLDS.performanceScore
  });

  checks.push({
    name: 'Accessibility Score',
    value: scores.accessibility,
    threshold: THRESHOLDS.accessibilityScore,
    unit: '',
    passed: scores.accessibility >= THRESHOLDS.accessibilityScore
  });

  // Metric checks
  checks.push({
    name: 'First Contentful Paint',
    value: metrics.firstContentfulPaint,
    threshold: THRESHOLDS.firstContentfulPaint,
    unit: 'ms',
    passed: metrics.firstContentfulPaint < THRESHOLDS.firstContentfulPaint
  });

  checks.push({
    name: 'Time to Interactive',
    value: metrics.timeToInteractive,
    threshold: THRESHOLDS.timeToInteractive,
    unit: 'ms',
    passed: metrics.timeToInteractive < THRESHOLDS.timeToInteractive
  });

  checks.push({
    name: 'Speed Index',
    value: metrics.speedIndex,
    threshold: THRESHOLDS.speedIndex,
    unit: 'ms',
    passed: metrics.speedIndex < THRESHOLDS.speedIndex
  });

  checks.push({
    name: 'Total Blocking Time',
    value: metrics.totalBlockingTime,
    threshold: THRESHOLDS.totalBlockingTime,
    unit: 'ms',
    passed: metrics.totalBlockingTime < THRESHOLDS.totalBlockingTime
  });

  checks.push({
    name: 'Cumulative Layout Shift',
    value: metrics.cumulativeLayoutShift.toFixed(3),
    threshold: THRESHOLDS.cumulativeLayoutShift,
    unit: '',
    passed: metrics.cumulativeLayoutShift < THRESHOLDS.cumulativeLayoutShift
  });

  checks.push({
    name: 'Largest Contentful Paint',
    value: metrics.largestContentfulPaint,
    threshold: THRESHOLDS.largestContentfulPaint,
    unit: 'ms',
    passed: metrics.largestContentfulPaint < THRESHOLDS.largestContentfulPaint
  });

  return checks;
}

/**
 * Print results to console
 */
function printResults(device, results, checks) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${device.toUpperCase()} PERFORMANCE RESULTS`);
  console.log(`${'='.repeat(60)}\n`);

  // Scores
  console.log('📊 SCORES:');
  console.log(`  Performance:    ${results.scores.performance}/100`);
  console.log(`  Accessibility:  ${results.scores.accessibility}/100`);
  console.log(`  Best Practices: ${results.scores.bestPractices}/100`);
  console.log(`  SEO:            ${results.scores.seo}/100\n`);

  // Metrics
  console.log('⚡ METRICS:');
  console.log(`  First Contentful Paint:    ${results.metrics.firstContentfulPaint}ms`);
  console.log(`  Speed Index:               ${results.metrics.speedIndex}ms`);
  console.log(`  Largest Contentful Paint:  ${results.metrics.largestContentfulPaint}ms`);
  console.log(`  Time to Interactive:       ${results.metrics.timeToInteractive}ms`);
  console.log(`  Total Blocking Time:       ${results.metrics.totalBlockingTime}ms`);
  console.log(`  Cumulative Layout Shift:   ${results.metrics.cumulativeLayoutShift.toFixed(3)}\n`);

  // Diagnostics
  console.log('🔍 DIAGNOSTICS:');
  console.log(`  Main Thread Work:  ${Math.round(results.diagnostics.mainThreadWork)}ms`);
  console.log(`  Bootup Time:       ${Math.round(results.diagnostics.bootupTime)}ms`);
  console.log(`  Network Requests:  ${results.diagnostics.networkRequests}`);
  console.log(`  Total Byte Weight: ${Math.round(results.diagnostics.totalByteWeight / 1024)}KB\n`);

  // Threshold checks
  console.log('✅ THRESHOLD CHECKS:');
  const allPassed = checks.every(check => check.passed);
  
  checks.forEach(check => {
    const icon = check.passed ? '✅' : '❌';
    const comparison = check.unit === '' ? '>=' : '<';
    console.log(`  ${icon} ${check.name}: ${check.value}${check.unit} ${comparison} ${check.threshold}${check.unit}`);
  });

  console.log(`\n${allPassed ? '✅ ALL CHECKS PASSED' : '❌ SOME CHECKS FAILED'}\n`);
  console.log(`${'='.repeat(60)}\n`);

  return allPassed;
}

/**
 * Save reports
 */
function saveReports(device, runnerResult) {
  // Create output directory if it doesn't exist
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Save HTML report
  const htmlPath = path.join(OUTPUT_DIR, `lighthouse-${device}-${TIMESTAMP}.html`);
  fs.writeFileSync(htmlPath, runnerResult.report[0]);
  console.log(`📄 HTML report saved: ${htmlPath}`);

  // Save JSON report
  const jsonPath = path.join(OUTPUT_DIR, `lighthouse-${device}-${TIMESTAMP}.json`);
  fs.writeFileSync(jsonPath, runnerResult.report[1]);
  console.log(`📄 JSON report saved: ${jsonPath}`);

  // Save summary
  const results = extractMetrics(runnerResult.lhr);
  const checks = checkThresholds(results);
  const summary = {
    timestamp: new Date().toISOString(),
    device,
    url: TARGET_URL,
    scores: results.scores,
    metrics: results.metrics,
    diagnostics: results.diagnostics,
    checks: checks.map(c => ({
      name: c.name,
      passed: c.passed,
      value: c.value,
      threshold: c.threshold
    })),
    allPassed: checks.every(c => c.passed)
  };

  const summaryPath = path.join(OUTPUT_DIR, `summary-${device}-${TIMESTAMP}.json`);
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  console.log(`📄 Summary saved: ${summaryPath}\n`);
}

/**
 * Main function
 */
async function main() {
  console.log('\n🎯 AFIRGen Performance Testing\n');
  console.log(`Target URL: ${TARGET_URL}`);
  console.log(`Timestamp: ${new Date().toISOString()}\n`);

  let allTestsPassed = true;

  try {
    // Test desktop
    const desktopResult = await runLighthouse(TARGET_URL, 'desktop');
    const desktopMetrics = extractMetrics(desktopResult.lhr);
    const desktopChecks = checkThresholds(desktopMetrics);
    const desktopPassed = printResults('desktop', desktopMetrics, desktopChecks);
    saveReports('desktop', desktopResult);
    allTestsPassed = allTestsPassed && desktopPassed;

    // Test mobile
    const mobileResult = await runLighthouse(TARGET_URL, 'mobile');
    const mobileMetrics = extractMetrics(mobileResult.lhr);
    const mobileChecks = checkThresholds(mobileMetrics);
    const mobilePassed = printResults('mobile', mobileMetrics, mobileChecks);
    saveReports('mobile', mobileResult);
    allTestsPassed = allTestsPassed && mobilePassed;

    // Final summary
    console.log('\n' + '='.repeat(60));
    console.log('  FINAL RESULTS');
    console.log('='.repeat(60) + '\n');
    console.log(`Desktop: ${desktopPassed ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`Mobile:  ${mobilePassed ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`\nOverall: ${allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}\n`);

    process.exit(allTestsPassed ? 0 : 1);
  } catch (error) {
    console.error('\n❌ Error running performance tests:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { runLighthouse, extractMetrics, checkThresholds };
