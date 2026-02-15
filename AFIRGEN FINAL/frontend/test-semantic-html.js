/**
 * Test script for semantic HTML and skip link implementation
 * Tests requirement 5.4.6: Skip links for navigation
 */

const fs = require('fs');
const path = require('path');

// Read the HTML file
const htmlPath = path.join(__dirname, 'index.html');
const html = fs.readFileSync(htmlPath, 'utf-8');

const results = [];

function addResult(testName, passed, message) {
    results.push({ testName, passed, message });
    const status = passed ? '✓ PASS' : '✗ FAIL';
    console.log(`${status} - ${testName}: ${message}`);
}

console.log('='.repeat(60));
console.log('Semantic HTML and Skip Link Tests');
console.log('Testing Requirement 5.4.6: Skip links for navigation');
console.log('='.repeat(60));
console.log();

// Test 1: Skip link exists
const hasSkipLink = html.includes('class="skip-link"');
addResult(
    'Skip Link Exists',
    hasSkipLink,
    hasSkipLink ? 'Skip link found with class "skip-link"' : 'Skip link not found'
);

// Test 2: Skip link has correct href
const skipLinkMatch = html.match(/<a[^>]*href="([^"]*)"[^>]*class="skip-link"[^>]*>|<a[^>]*class="skip-link"[^>]*href="([^"]*)"[^>]*>/);
const skipLinkHref = skipLinkMatch ? (skipLinkMatch[1] || skipLinkMatch[2]) : null;
addResult(
    'Skip Link Target',
    skipLinkHref === '#main-content',
    skipLinkHref === '#main-content' 
        ? 'Skip link points to #main-content' 
        : `Skip link points to ${skipLinkHref || 'nothing'}`
);

// Test 3: Skip link text is descriptive
const skipLinkTextMatch = html.match(/<a[^>]*class="skip-link"[^>]*>([^<]*)<\/a>/);
const skipLinkText = skipLinkTextMatch ? skipLinkTextMatch[1].trim() : null;
addResult(
    'Skip Link Text',
    skipLinkText === 'Skip to main content',
    skipLinkText === 'Skip to main content'
        ? 'Skip link has descriptive text'
        : `Skip link text is "${skipLinkText}"`
);

// Test 4: Main content uses <main> tag
const hasMainElement = html.includes('<main');
addResult(
    'Main Element',
    hasMainElement,
    hasMainElement ? '<main> element found' : '<main> element not found'
);

// Test 5: Main element has id="main-content"
const mainIdMatch = html.match(/<main[^>]*id="main-content"[^>]*>/);
addResult(
    'Main Element ID',
    mainIdMatch !== null,
    mainIdMatch !== null
        ? '<main> has id="main-content"'
        : '<main> does not have id="main-content"'
);

// Test 6: Sidebar uses <aside> tag
const hasAsideElement = html.includes('<aside');
addResult(
    'Aside Element',
    hasAsideElement,
    hasAsideElement ? '<aside> element found for sidebar' : '<aside> element not found'
);

// Test 7: Nav uses <nav> tag
const hasNavElement = html.includes('<nav');
addResult(
    'Nav Element',
    hasNavElement,
    hasNavElement ? '<nav> element found' : '<nav> element not found'
);

// Test 8: Nav items use <button> tags (not <div>)
const navButtonMatches = html.match(/<button[^>]*class="nav-item"[^>]*>/g) || [];
const navDivMatches = html.match(/<div[^>]*class="nav-item"[^>]*>/g) || [];
addResult(
    'Nav Items Use Buttons',
    navButtonMatches.length > 0 && navDivMatches.length === 0,
    navButtonMatches.length > 0 && navDivMatches.length === 0
        ? `Found ${navButtonMatches.length} button nav items, 0 div nav items`
        : `Found ${navButtonMatches.length} button nav items, ${navDivMatches.length} div nav items`
);

// Test 9: All buttons have type attribute
const buttonMatches = html.match(/<button[^>]*>/g) || [];
const buttonsWithoutType = buttonMatches.filter(btn => !btn.includes('type='));
addResult(
    'Buttons Have Type',
    buttonsWithoutType.length === 0,
    buttonsWithoutType.length === 0
        ? `All ${buttonMatches.length} buttons have type attribute`
        : `${buttonsWithoutType.length} of ${buttonMatches.length} buttons missing type attribute`
);

// Test 10: Main has role="main"
const mainRoleMatch = html.match(/<main[^>]*role="main"[^>]*>/);
addResult(
    'Main Role',
    mainRoleMatch !== null,
    mainRoleMatch !== null
        ? '<main> has role="main"'
        : '<main> does not have role="main"'
);

// Test 11: Aside has role="complementary"
const asideRoleMatch = html.match(/<aside[^>]*role="complementary"[^>]*>/);
addResult(
    'Aside Role',
    asideRoleMatch !== null,
    asideRoleMatch !== null
        ? '<aside> has role="complementary"'
        : '<aside> does not have role="complementary"'
);

// Test 12: Skip link is positioned before navbar
const skipLinkIndex = html.indexOf('class="skip-link"');
const navbarIndex = html.indexOf('class="navbar"');
addResult(
    'Skip Link Position',
    skipLinkIndex < navbarIndex && skipLinkIndex > 0,
    skipLinkIndex < navbarIndex && skipLinkIndex > 0
        ? 'Skip link appears before navbar in DOM'
        : 'Skip link should appear before navbar'
);

// Summary
console.log();
console.log('='.repeat(60));
const passed = results.filter(r => r.passed).length;
const total = results.length;
console.log(`Summary: ${passed}/${total} tests passed`);
console.log('='.repeat(60));

// Exit with appropriate code
process.exit(passed === total ? 0 : 1);
