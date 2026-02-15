# PWA Installation Testing Guide

## Overview
This guide provides instructions for testing the Progressive Web App (PWA) installation functionality of AFIRGen.

## Prerequisites
- HTTPS connection (required for PWA)
- Modern browser (Chrome, Edge, Safari, Firefox)
- Service worker registered and active

## Testing on Chrome Desktop

1. **Open the application** in Chrome
2. **Check for install prompt**:
   - Look for install icon in address bar (right side)
   - Or check for toast notification about installation
3. **Install the app**:
   - Click the install icon in address bar
   - Or use Chrome menu → "Install AFIRGen"
   - Or call `window.promptPWAInstall()` in console
4. **Verify installation**:
   - App should open in standalone window
   - Check chrome://apps to see installed app
   - Verify app icon appears in taskbar/dock

## Testing on Chrome Mobile (Android)

1. **Open the application** in Chrome mobile
2. **Check for install banner**:
   - Look for "Add to Home Screen" banner at bottom
   - Or check for toast notification
3. **Install the app**:
   - Tap "Add to Home Screen" banner
   - Or use Chrome menu → "Add to Home Screen"
4. **Verify installation**:
   - App icon should appear on home screen
   - Tap icon to launch app in standalone mode
   - Verify splash screen appears on launch

## Testing on Safari (iOS)

1. **Open the application** in Safari
2. **Manual installation** (iOS doesn't support beforeinstallprompt):
   - Tap Share button (square with arrow)
   - Scroll and tap "Add to Home Screen"
   - Customize name if desired
   - Tap "Add"
3. **Verify installation**:
   - App icon should appear on home screen
   - Tap icon to launch app
   - Verify app runs in standalone mode

## Testing Offline Functionality

1. **Install the app** using steps above
2. **Open the installed app**
3. **Go offline**:
   - Turn off WiFi and mobile data
   - Or use DevTools → Network → Offline
4. **Verify offline functionality**:
   - App should still load
   - Cached pages should be accessible
   - Toast notification should indicate offline status
5. **Go back online**:
   - Restore connection
   - Verify toast notification indicates online status
   - Verify sync functionality works

## Verification Checklist

- [ ] Install prompt appears on supported browsers
- [ ] Install prompt can be triggered programmatically
- [ ] App installs successfully on desktop
- [ ] App installs successfully on mobile
- [ ] Installed app opens in standalone window
- [ ] App icon displays correctly
- [ ] Splash screen appears on mobile
- [ ] App works offline after installation
- [ ] Service worker caches assets correctly
- [ ] Online/offline status notifications work
- [ ] App updates when new version available

## Troubleshooting

### Install prompt doesn't appear
- Verify HTTPS connection
- Check manifest.json is accessible
- Verify service worker is registered
- Check browser console for errors
- Ensure app meets PWA criteria (Lighthouse audit)

### App doesn't work offline
- Verify service worker is active
- Check cache storage in DevTools
- Verify fetch event handler in sw.js
- Check network requests in DevTools

### Icons don't display
- Verify icon files exist in /assets/
- Check manifest.json icon paths
- Verify icon sizes are correct (192x192, 512x512)
- Check browser console for 404 errors

## Notes

- PWA installation requires HTTPS (except localhost)
- iOS Safari doesn't support beforeinstallprompt event
- Some browsers may have different install UI
- Service worker must be registered before installation
- Manifest.json must be valid and accessible

## Testing Complete

Once all items in the verification checklist are confirmed, Task 20.4 is complete.
