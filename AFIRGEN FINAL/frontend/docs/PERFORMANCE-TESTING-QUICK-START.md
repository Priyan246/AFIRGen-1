# Performance Testing Quick Start

## Quick Commands

### 1. Build and Verify Bundle Sizes
```bash
# Build production bundle
npm run build

# Check bundle sizes
npm run test:bundle-size
```

### 2. Run Lighthouse Audit
```bash
# Start server (in one terminal)
npm start

# Run Lighthouse (in another terminal)
npm run test:lighthouse
```

### 3. Run Automated Performance Tests
```bash
# Start server (in one terminal)
npm start

# Run automated tests (in another terminal)
npm run test:performance
```

### 4. Run Lighthouse CI
```bash
# Start server
npm start

# Run Lighthouse CI (requires @lhci/cli installed globally)
npm run test:lighthouse-ci
```

## Current Performance Status

### Bundle Sizes (as of last check)
- ✅ CSS: 4.47 KB / 50 KB (8.9%)
- ✅ App JS: 12.16 KB / 100 KB (12.2%)
- ✅ Lib JS: 8.02 KB / 150 KB (5.3%)
- ✅ Total: 31.34 KB / 500 KB (6.3%)

**Status**: All bundle size checks PASSED ✅

### Performance Targets
- Performance Score: >90
- First Contentful Paint: <1s
- Time to Interactive: <3s
- Speed Index: <2s
- Total Blocking Time: <300ms
- Cumulative Layout Shift: <0.1
- Largest Contentful Paint: <2.5s

## Testing Workflow

### Before Release
1. Build production bundle: `npm run build`
2. Check bundle sizes: `npm run test:bundle-size`
3. Start server: `npm start`
4. Run Lighthouse audit: `npm run test:lighthouse`
5. Review reports in `performance-reports/` directory
6. Verify all metrics meet targets

### During Development
1. Build: `npm run build`
2. Start dev server: `npm run dev`
3. Open Chrome DevTools
4. Go to Lighthouse tab
5. Run quick audit
6. Check for regressions

### CI/CD Integration
1. Add Lighthouse CI to your pipeline
2. Use `npm run test:lighthouse-ci`
3. Set up GitHub Actions (see PERFORMANCE-TESTING-GUIDE.md)
4. Monitor performance over time

## Troubleshooting

### Server Not Running
```bash
# Check if server is running
curl http://localhost:3000

# If not, start it
npm start
```

### Lighthouse Not Installed
```bash
# Install globally
npm install -g lighthouse

# Or use npx
npx lighthouse http://localhost:3000 --view
```

### Bundle Size Too Large
1. Check detailed breakdown: `npm run test:bundle-size`
2. Identify large files
3. Consider:
   - Code splitting
   - Lazy loading
   - Removing unused dependencies
   - Tree shaking

### Performance Score Low
1. Review Lighthouse report
2. Check "Opportunities" section
3. Check "Diagnostics" section
4. Common fixes:
   - Optimize images
   - Minify code
   - Enable caching
   - Reduce JavaScript execution time

## Resources

- Full Guide: [PERFORMANCE-TESTING-GUIDE.md](./PERFORMANCE-TESTING-GUIDE.md)
- Asset Optimization: [ASSET-OPTIMIZATION-GUIDE.md](./ASSET-OPTIMIZATION-GUIDE.md)
- Lighthouse Documentation: https://developers.google.com/web/tools/lighthouse
- Web.dev Performance: https://web.dev/performance/
