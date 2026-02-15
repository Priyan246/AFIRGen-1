# Screen Reader Testing Guide

## Overview
This guide provides instructions for testing AFIRGen with screen readers to ensure WCAG 2.1 AA compliance and optimal accessibility.

## Prerequisites
- Screen reader software installed (NVDA for Windows, VoiceOver for macOS/iOS)
- AFIRGen application running locally or on test server
- Basic familiarity with screen reader navigation

## Testing with NVDA (Windows)

### Installation
1. Download NVDA from https://www.nvaccess.org/download/
2. Install and launch NVDA
3. NVDA will start reading automatically

### Basic Navigation
- **Start/Stop NVDA**: Ctrl + Alt + N
- **Read next item**: Down Arrow
- **Read previous item**: Up Arrow
- **Read all**: Insert + Down Arrow
- **Stop reading**: Ctrl
- **Navigate by headings**: H (next), Shift + H (previous)
- **Navigate by buttons**: B (next), Shift + B (previous)
- **Navigate by forms**: F (next), Shift + F (previous)
- **Navigate by links**: K (next), Shift + K (previous)

### Test Scenarios

#### 1. Page Load and Structure
- [ ] NVDA announces page title on load
- [ ] Skip link is announced and functional
- [ ] Landmarks (navigation, main, complementary) are announced
- [ ] Headings hierarchy is logical (H1 → H2 → H3)

#### 2. File Upload
- [ ] File upload buttons are announced with labels
- [ ] Drag-and-drop zones are announced
- [ ] File validation errors are announced immediately
- [ ] Success messages are announced after upload

#### 3. FIR Generation
- [ ] Generate button state (enabled/disabled) is announced
- [ ] Loading states are announced ("Loading: Uploading files...")
- [ ] Progress updates are announced
- [ ] Completion is announced ("Complete: Loading complete")

#### 4. Modal Dialogs
- [ ] Modal opening is announced ("Dialog opened: [title]")
- [ ] Focus moves to modal content
- [ ] Modal content is readable
- [ ] Buttons and inputs are announced with labels
- [ ] Modal closing is announced ("Dialog closed")
- [ ] Focus returns to trigger element

#### 5. Toast Notifications
- [ ] Success toasts are announced ("Success: [message]")
- [ ] Error toasts are announced ("Error: [message]")
- [ ] Info toasts are announced
- [ ] Toasts don't interrupt current reading

#### 6. FIR History
- [ ] FIR list is announced as a list
- [ ] List items are announced with status
- [ ] Search input is announced with label
- [ ] Filter dropdowns are announced with labels
- [ ] Pagination controls are announced

#### 7. Dark Mode Toggle
- [ ] Toggle button is announced with current state
- [ ] State change is announced after toggle

## Testing with VoiceOver (macOS)

### Activation
- **Enable VoiceOver**: Cmd + F5
- **Disable VoiceOver**: Cmd + F5

### Basic Navigation
- **VoiceOver modifier**: Ctrl + Option (VO)
- **Read next item**: VO + Right Arrow
- **Read previous item**: VO + Left Arrow
- **Read all**: VO + A
- **Stop reading**: Ctrl
- **Navigate by headings**: VO + Cmd + H
- **Navigate by buttons**: VO + Cmd + J
- **Navigate by forms**: VO + Cmd + J
- **Navigate by links**: VO + Cmd + L

### Test Scenarios
(Same as NVDA test scenarios above)

## Testing with VoiceOver (iOS)

### Activation
1. Go to Settings → Accessibility → VoiceOver
2. Toggle VoiceOver on
3. Or use Siri: "Hey Siri, turn on VoiceOver"

### Basic Navigation
- **Swipe right**: Next item
- **Swipe left**: Previous item
- **Double tap**: Activate item
- **Two-finger swipe up**: Read all from current position
- **Two-finger tap**: Stop reading
- **Rotor**: Rotate two fingers to change navigation mode

### Test Scenarios
(Same as NVDA test scenarios above, adapted for touch)

## Verification Checklist

### Content Accessibility
- [ ] All images have alt text or aria-label
- [ ] All buttons have accessible names
- [ ] All form inputs have labels
- [ ] All links have descriptive text
- [ ] Decorative elements have aria-hidden="true"

### ARIA Attributes
- [ ] ARIA live regions work correctly
- [ ] ARIA labels are descriptive
- [ ] ARIA roles are appropriate
- [ ] ARIA states (aria-busy, aria-disabled) update correctly
- [ ] ARIA properties (aria-labelledby, aria-describedby) are correct

### Focus Management
- [ ] Focus order is logical
- [ ] Focus is visible (2px outline)
- [ ] Focus trap works in modals
- [ ] Focus returns after modal close
- [ ] Skip link works correctly

### Announcements
- [ ] Status changes are announced
- [ ] Errors are announced immediately
- [ ] Success messages are announced
- [ ] Loading states are announced
- [ ] Completion is announced

### Keyboard Navigation
- [ ] All functionality accessible via keyboard
- [ ] Tab order is logical
- [ ] Enter/Space activate buttons
- [ ] Escape closes modals
- [ ] Arrow keys work in lists/dropdowns

## Common Issues and Solutions

### Issue: Announcements not heard
**Solution**: 
- Check ARIA live regions are present in DOM
- Verify aria-live attribute is set correctly
- Ensure content changes trigger announcements
- Check browser console for errors

### Issue: Focus not trapped in modal
**Solution**:
- Verify focus-management.js is loaded
- Check modal has focusable elements
- Ensure Tab key handler is working
- Test with different browsers

### Issue: Labels not announced
**Solution**:
- Check aria-label or aria-labelledby is present
- Verify label text is not empty
- Ensure label is associated with correct element
- Check for duplicate IDs

### Issue: Screen reader reads too much
**Solution**:
- Add aria-hidden="true" to decorative elements
- Use aria-atomic="true" for live regions
- Simplify complex structures
- Use semantic HTML

## Testing Complete

Once all items in the verification checklist are confirmed across NVDA and VoiceOver, Task 21.4 is complete.

## Additional Resources

- NVDA User Guide: https://www.nvaccess.org/files/nvda/documentation/userGuide.html
- VoiceOver User Guide: https://support.apple.com/guide/voiceover/welcome/mac
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
