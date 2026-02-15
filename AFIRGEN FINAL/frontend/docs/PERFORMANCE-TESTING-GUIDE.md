# Performance Testing Guide

## Overview

This guide provides instructions for running performance tests on the AFIRGen frontend application to ensure it meets the performance requirements specified in the design document.

## Performance Requirements

### Target Metrics
- **Page load time**: <2 seconds on 3G
- **Time to Interactive (TTI)**: <3 seconds
- **First Contentful Paint (FCP)**: <1 second
- **Lighthouse performance score**: >90
- **Bundle size**: <500KB (gzipped)

## Prerequisites

1. **Build the application**:
```bash
npm run build
```

2. **Start a local server**:
```bash
npm start
# Server runs on http://localhost:3000
```

## 1. Lighthouse Audit

### Using Chrome DevTools

1. Open Chrome and navigate to `http://localhost:3000`
2. Open DevTools (F12 or Ctrl+Shift+I)
3. Go to the "Lighthouse" tab
4. Select categories:
   - ✅ Performance
   - ✅ Accessibility
   - ✅ Best Practices
   - ✅ SEO
5. Select device: Desktop or Mobile
6. Click "Analyze page load"

### Using Lighthouse CLI

Install Lighthouse globally:
```bash
npm install -g lighthouse
```

Run Lighthouse audit:
```bash
# Desktop audit
lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report-desktop.html --preset=desktop --view

# Mobile audit
lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report-mobile.html --view

# JSON output for CI/CD
lighthouse http://localhost:3000 --output json --output-path ./lighthouse-report.json
```

### Lighthouse CI (Automated)

For continuous integration, use Lighthouse CI:

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Run Lighthouse CI
lhci autorun --config=lighthouserc.json
```

Create `lighthouserc.json`:
```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000"],
      "numberOfRuns": 3
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", {"minScore": 0.9}],
        "categories:accessibility": ["error", {"minScore": 0.9}],
        "first-contentful-paint": ["error", {"maxNumericValue": 1000}],
        "interactive": ["error", {"maxNumericValue": 3000}],
        "speed-index": ["error", {"maxNumericValue": 2000}]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### Expected Results

**Performance Metrics:**
- Performance Score: >90
- First Contentful Paint: <1s
- Time to Interactive: <3s
- Speed Index: <2s
- Total Blocking Time: <300ms
- Cumulative Layout Shift: <0.1
- Largest Contentful Paint: <2.5s

**Opportunities:**
- All images optimized (WebP)
- Text compression enabled (gzip/brotli)
- Unused JavaScript removed
- Efficient cache policy

**Diagnostics:**
- Minimize main-thread work
- Reduce JavaScript execution time
- Avoid enormous network payloads

## 2. Network Throttling Test (3G)

### Using Chrome DevTools

1. Open DevTools (F12)
2. Go to "Network" tab
3. Click "No throttling" dropdown
4. Select "Slow 3G" or "Fast 3G"
5. Reload the page (Ctrl+R)
6. Observe:
   - Page load time
   - Time to interactive
   - User experience

### Using Lighthouse with 3G Throttling

```bash
lighthouse http://localhost:3000 \
  --throttling-method=devtools \
  --throttling.rttMs=150 \
  --throttling.throughputKbps=1638.4 \
  --throttling.cpuSlowdownMultiplier=4 \
  --view
```

### Expected Results on 3G
- Page load: <2 seconds
- FCP: <1.5 seconds
- TTI: <3 seconds
- App remains usable
- Loading states visible
- No layout shifts

## 3. Bundle Size Analysis

### Using npm script

```bash
npm run verify:sizes
```

This will output:
```
CSS: XX.XX KB
App JS: XX.XX KB
Lib JS: XX.XX KB
HTML: XX.XX KB
Total: XXX.XX KB
Est. gzipped: XX.XX KB
```

### Manual Verification

```bash
# Check gzipped sizes (Windows PowerShell)
Get-ChildItem -Path dist -Recurse -File | ForEach-Object {
    $gzipSize = (Get-Content $_.FullName -Raw | 
                 ForEach-Object { [System.IO.Compression.GZipStream]::new(
                     [System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($_)),
                     [System.IO.Compression.CompressionMode]::Compress
                 ).Length })
    [PSCustomObject]@{
        File = $_.Name
        Original = "{0:N2} KB" -f ($_.Length / 1KB)
        Gzipped = "{0:N2} KB" -f ($gzipSize / 1KB)
    }
} | Format-Table -AutoSize
```

### Using webpack-bundle-analyzer (if using webpack)

```bash
npm install --save-dev webpack-bundle-analyzer
```

Add to webpack config:
```javascript
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin()
  ]
};
```

### Expected Bundle Sizes
- **main.css**: <50KB (gzipped)
- **app.js**: <100KB (gzipped)
- **vendor.js** (DOMPurify + libs): <150KB (gzipped)
- **Total**: <500KB (gzipped)

## 4. WebPageTest

WebPageTest provides detailed performance analysis from real devices and locations.

### Using WebPageTest.org

1. Go to https://www.webpagetest.org/
2. Enter URL (requires public URL or ngrok tunnel)
3. Select test location (e.g., "Dulles, VA - Chrome")
4. Select connection speed (e.g., "3G", "4G", "Cable")
5. Click "Start Test"

### Using WebPageTest API

```bash
# Install webpagetest CLI
npm install -g webpagetest

# Run test
webpagetest test http://your-public-url.com \
  --key YOUR_API_KEY \
  --location Dulles:Chrome \
  --connectivity 3G \
  --runs 3
```

### Expected WebPageTest Results
- **First Byte Time**: <200ms
- **Start Render**: <1s
- **Speed Index**: <2s
- **Fully Loaded**: <3s
- **Requests**: <50
- **Bytes In**: <500KB

## 5. Chrome DevTools Performance Panel

### Recording Performance

1. Open DevTools (F12)
2. Go to "Performance" tab
3. Click record button (or Ctrl+E)
4. Reload page (Ctrl+R)
5. Stop recording after page loads
6. Analyze:
   - Main thread activity
   - JavaScript execution time
   - Layout/Paint operations
   - Network requests

### Key Metrics to Check
- **Scripting time**: <500ms
- **Rendering time**: <100ms
- **Painting time**: <50ms
- **Loading time**: <1s
- **Idle time**: Should be >50% after load

### Performance Bottlenecks to Look For
- Long tasks (>50ms)
- Excessive JavaScript execution
- Layout thrashing
- Large DOM size
- Unoptimized images
- Render-blocking resources

## 6. Core Web Vitals

### Measuring Core Web Vitals

**Largest Contentful Paint (LCP)**
- Target: <2.5s
- Measures: Loading performance
- Check: Largest element render time

**First Input Delay (FID)**
- Target: <100ms
- Measures: Interactivity
- Check: Time from first interaction to response

**Cumulative Layout Shift (CLS)**
- Target: <0.1
- Measures: Visual stability
- Check: Unexpected layout shifts

### Using web-vitals Library

Install:
```bash
npm install web-vitals
```

Add to your app:
```javascript
import {getCLS, getFID, getFCP, getLCP, getTTFB} from 'web-vitals';

function sendToAnalytics(metric) {
  console.log(metric);
  // Send to analytics service
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

## 7. Automated Performance Testing Script

Create `scripts/performance-test.js`:

```javascript
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');

async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({chromeFlags: ['--headless']});
  const options = {
    logLevel: 'info',
    output: 'html',
    onlyCategories: ['performance', 'accessibility'],
    port: chrome.port
  };
  
  const runnerResult = await lighthouse(url, options);
  
  // Extract scores
  const performanceScore = runnerResult.lhr.categories.performance.score * 100;
  const accessibilityScore = runnerResult.lhr.categories.accessibility.score * 100;
  
  // Extract metrics
  const metrics = runnerResult.lhr.audits.metrics.details.items[0];
  const fcp = metrics.firstContentfulPaint;
  const tti = metrics.interactive;
  const speedIndex = metrics.speedIndex;
  
  console.log('\n=== Lighthouse Results ===');
  console.log(`Performance Score: ${performanceScore}`);
  console.log(`Accessibility Score: ${accessibilityScore}`);
  console.log(`First Contentful Paint: ${fcp}ms`);
  console.log(`Time to Interactive: ${tti}ms`);
  console.log(`Speed Index: ${speedIndex}`);
  
  // Check if meets requirements
  const passed = 
    performanceScore >= 90 &&
    fcp < 1000 &&
    tti < 3000;
  
  console.log(`\n${passed ? '✅ PASSED' : '❌ FAILED'} - Performance requirements`);
  
  // Save report
  fs.writeFileSync('lighthouse-report.html', runnerResult.report);
  console.log('\nReport saved to lighthouse-report.html');
  
  await chrome.kill();
  
  return passed;
}

// Run test
runLighthouse('http://localhost:3000')
  .then(passed => process.exit(passed ? 0 : 1))
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
```

Add to package.json:
```json
{
  "scripts": {
    "test:performance": "node scripts/performance-test.js"
  },
  "devDependencies": {
    "lighthouse": "^10.0.0",
    "chrome-launcher": "^0.15.0"
  }
}
```

Run:
```bash
npm run test:performance
```

## 8. Performance Budget

Create `.perfbudget.json`:

```json
{
  "budget": [
    {
      "resourceSizes": [
        {
          "resourceType": "script",
          "budget": 150
        },
        {
          "resourceType": "stylesheet",
          "budget": 50
        },
        {
          "resourceType": "image",
          "budget": 100
        },
        {
          "resourceType": "font",
          "budget": 50
        },
        {
          "resourceType": "total",
          "budget": 500
        }
      ]
    },
    {
      "timings": [
        {
          "metric": "first-contentful-paint",
          "budget": 1000
        },
        {
          "metric": "interactive",
          "budget": 3000
        },
        {
          "metric": "speed-index",
          "budget": 2000
        }
      ]
    }
  ]
}
```

## 9. Continuous Performance Monitoring

### GitHub Actions Workflow

Create `.github/workflows/performance.yml`:

```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Start server
        run: npm start &
        
      - name: Wait for server
        run: npx wait-on http://localhost:3000
      
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: lighthouse-results
          path: .lighthouseci
```

## 10. Performance Checklist

### Before Testing
- [ ] Build production bundle (`npm run build`)
- [ ] Start local server (`npm start`)
- [ ] Clear browser cache
- [ ] Close unnecessary browser tabs
- [ ] Disable browser extensions

### During Testing
- [ ] Run Lighthouse audit (desktop and mobile)
- [ ] Test on 3G network throttling
- [ ] Verify bundle sizes
- [ ] Check Core Web Vitals
- [ ] Test on real devices (if possible)

### After Testing
- [ ] Performance score >90
- [ ] FCP <1s
- [ ] TTI <3s
- [ ] Bundle size <500KB gzipped
- [ ] No console errors
- [ ] All resources loaded successfully

### If Tests Fail
1. Identify bottlenecks from Lighthouse report
2. Check "Opportunities" section for improvements
3. Review "Diagnostics" for issues
4. Optimize identified resources
5. Re-run tests

## 11. Common Performance Issues and Fixes

### Issue: Low Performance Score

**Possible Causes:**
- Large JavaScript bundles
- Render-blocking resources
- Unoptimized images
- No caching

**Fixes:**
- Code splitting
- Lazy loading
- Image optimization
- Service worker caching

### Issue: High FCP/LCP

**Possible Causes:**
- Large CSS files
- Render-blocking scripts
- Slow server response
- Large images above fold

**Fixes:**
- Critical CSS inline
- Defer non-critical scripts
- CDN for static assets
- Optimize hero images

### Issue: High TTI

**Possible Causes:**
- Too much JavaScript
- Long tasks blocking main thread
- Third-party scripts

**Fixes:**
- Code splitting
- Web workers for heavy tasks
- Defer third-party scripts
- Reduce JavaScript execution time

### Issue: High CLS

**Possible Causes:**
- Images without dimensions
- Dynamic content insertion
- Web fonts causing layout shift

**Fixes:**
- Set width/height on images
- Reserve space for dynamic content
- Use font-display: swap

## 12. Tools and Resources

### Performance Testing Tools
- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **WebPageTest**: https://www.webpagetest.org/
- **GTmetrix**: https://gtmetrix.com/
- **PageSpeed Insights**: https://pagespeed.web.dev/

### Monitoring Tools
- **Chrome DevTools**: Built into Chrome
- **Firefox Developer Tools**: Built into Firefox
- **web-vitals**: https://github.com/GoogleChrome/web-vitals

### Analysis Tools
- **webpack-bundle-analyzer**: Bundle size analysis
- **source-map-explorer**: JavaScript bundle analysis
- **Coverage tool**: Chrome DevTools Coverage tab

## 13. References

- [Web.dev Performance](https://web.dev/performance/)
- [Lighthouse Scoring Guide](https://web.dev/performance-scoring/)
- [Core Web Vitals](https://web.dev/vitals/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
