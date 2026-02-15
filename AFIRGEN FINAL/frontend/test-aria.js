/**
 * ARIA Labels Test Script
 * Tests that all interactive elements have proper ARIA labels
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function testARIALabels() {
  log('\n=== ARIA Labels Accessibility Test ===\n', 'bold');
  
  const htmlPath = path.join(__dirname, 'index.html');
  const html = fs.readFileSync(htmlPath, 'utf-8');
  
  const tests = [];
  let passCount = 0;
  
  // Test 1: Navigation has role and aria-label
  const navMatch = html.match(/<nav[^>]*>/);
  if (navMatch) {
    const navTag = navMatch[0];
    const hasRole = navTag.includes('role="navigation"');
    const hasAriaLabel = navTag.includes('aria-label=');
    
    tests.push({
      name: 'Navigation has role="navigation"',
      pass: hasRole,
      details: hasRole ? 'Found role="navigation"' : 'Missing role attribute'
    });
    
    tests.push({
      name: 'Navigation has aria-label',
      pass: hasAriaLabel,
      details: hasAriaLabel ? 'Found aria-label' : 'Missing aria-label'
    });
  }
  
  // Test 2: All buttons have aria-label
  const buttonMatches = html.match(/<button[^>]*>/g) || [];
  const buttonsWithoutLabel = buttonMatches.filter(btn => 
    !btn.includes('aria-label=') && !btn.includes('aria-labelledby=')
  );
  tests.push({
    name: 'All buttons have aria-label',
    pass: buttonsWithoutLabel.length === 0,
    details: buttonsWithoutLabel.length === 0 
      ? `All ${buttonMatches.length} buttons have labels` 
      : `${buttonsWithoutLabel.length}/${buttonMatches.length} buttons missing labels`
  });
  
  // Test 3: File inputs have aria-label or aria-describedby
  const fileInputMatches = html.match(/<input[^>]*type="file"[^>]*>/g) || [];
  const inputsWithoutLabel = fileInputMatches.filter(input => 
    !input.includes('aria-label=') && !input.includes('aria-describedby=')
  );
  tests.push({
    name: 'All file inputs have ARIA labels',
    pass: inputsWithoutLabel.length === 0,
    details: inputsWithoutLabel.length === 0 
      ? `All ${fileInputMatches.length} file inputs have labels` 
      : `${inputsWithoutLabel.length}/${fileInputMatches.length} inputs missing labels`
  });
  
  // Test 4: Decorative SVG icons have aria-hidden
  const svgMatches = html.match(/<svg[^>]*>/g) || [];
  const svgsWithoutHidden = svgMatches.filter(svg => !svg.includes('aria-hidden="true"'));
  tests.push({
    name: 'Decorative icons have aria-hidden="true"',
    pass: svgsWithoutHidden.length === 0,
    details: svgsWithoutHidden.length === 0 
      ? `All ${svgMatches.length} icons properly hidden` 
      : `${svgsWithoutHidden.length}/${svgMatches.length} icons not hidden`
  });
  
  // Test 5: Main content has role="main"
  const hasMainRole = html.includes('role="main"');
  tests.push({
    name: 'Main content has role="main"',
    pass: hasMainRole,
    details: hasMainRole ? 'Main landmark found' : 'Main landmark not found'
  });
  
  // Test 6: Sidebar has role="complementary"
  const hasComplementaryRole = html.includes('role="complementary"');
  tests.push({
    name: 'Sidebar has role="complementary"',
    pass: hasComplementaryRole,
    details: hasComplementaryRole ? 'Complementary landmark found' : 'Complementary landmark not found'
  });
  
  // Test 7: Modal has proper ARIA attributes
  const modalMatch = html.match(/<div[^>]*id="modal-overlay"[^>]*>/);
  if (modalMatch) {
    const modalTag = modalMatch[0];
    const hasDialogRole = modalTag.includes('role="dialog"');
    const hasAriaModal = modalTag.includes('aria-modal="true"');
    
    tests.push({
      name: 'Modal has role="dialog" and aria-modal="true"',
      pass: hasDialogRole && hasAriaModal,
      details: hasDialogRole && hasAriaModal 
        ? 'Modal properly configured' 
        : 'Modal missing ARIA attributes'
    });
  }
  
  // Test 8: Live regions are present
  const liveRegionMatches = html.match(/aria-live=/g) || [];
  tests.push({
    name: 'Live regions are present',
    pass: liveRegionMatches.length > 0,
    details: `Found ${liveRegionMatches.length} live regions`
  });
  
  // Test 9: Nav items have role="menuitem"
  const navItemMatches = html.match(/<div[^>]*class="nav-item"[^>]*>/g) || [];
  const navItemsWithRole = navItemMatches.filter(item => item.includes('role="menuitem"'));
  tests.push({
    name: 'Navigation items have role="menuitem"',
    pass: navItemsWithRole.length === navItemMatches.length,
    details: `${navItemsWithRole.length}/${navItemMatches.length} nav items have menuitem role`
  });
  
  // Test 10: Search input has aria-label
  const searchInputMatch = html.match(/<input[^>]*id="search-input"[^>]*>/);
  if (searchInputMatch) {
    const hasAriaLabel = searchInputMatch[0].includes('aria-label=');
    tests.push({
      name: 'Search input has aria-label',
      pass: hasAriaLabel,
      details: hasAriaLabel ? 'Search input has aria-label' : 'Search input missing aria-label'
    });
  }
  
  // Test 11: FIR list has role="list"
  const hasFirListRole = html.includes('class="fir-list"') && html.includes('role="list"');
  tests.push({
    name: 'FIR list has role="list"',
    pass: hasFirListRole,
    details: hasFirListRole ? 'FIR list has proper role' : 'FIR list missing role'
  });
  
  // Test 12: Status messages have role="status"
  const statusMatches = html.match(/<div[^>]*class="status-message[^>]*>/g) || [];
  const statusWithRole = statusMatches.filter(status => status.includes('role="status"'));
  tests.push({
    name: 'Status messages have role="status"',
    pass: statusWithRole.length === statusMatches.length,
    details: `${statusWithRole.length}/${statusMatches.length} status messages have role`
  });
  
  // Display results
  tests.forEach(test => {
    if (test.pass) {
      passCount++;
      log(`✓ ${test.name}`, 'green');
      log(`  ${test.details}`, 'blue');
    } else {
      log(`✗ ${test.name}`, 'red');
      log(`  ${test.details}`, 'yellow');
    }
  });
  
  log(`\n=== Summary ===`, 'bold');
  log(`${passCount}/${tests.length} tests passed`, passCount === tests.length ? 'green' : 'yellow');
  
  if (passCount === tests.length) {
    log('\n✓ All ARIA labels are properly implemented!', 'green');
    return 0;
  } else {
    log(`\n✗ ${tests.length - passCount} test(s) failed`, 'red');
    return 1;
  }
}

// Run tests
const exitCode = testARIALabels();
process.exit(exitCode);
