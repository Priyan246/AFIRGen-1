# jsPDF Library Download Instructions

## Required Library
- **Library:** jsPDF
- **Version:** 2.5.1 or later
- **File:** jspdf.umd.min.js

## Download Options

### Option 1: CDN (Quick Setup)
Add this script tag to `index.html` before `pdf.js`:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
```

### Option 2: NPM (Recommended for Production)
```bash
npm install jspdf
# Copy from node_modules to lib folder
cp node_modules/jspdf/dist/jspdf.umd.min.js lib/jspdf.min.js
```

### Option 3: Direct Download
1. Visit: https://github.com/parallax/jsPDF/releases
2. Download latest release
3. Extract `jspdf.umd.min.js`
4. Save to `AFIRGEN FINAL/frontend/lib/jspdf.min.js`

## Integration

After downloading, add to `index.html`:
```html
<!-- PDF Export library -->
<script src="lib/jspdf.min.js"></script>
<script src="js/pdf.js"></script>
```

## Verification

Open browser console and check:
```javascript
console.log(window.jspdf); // Should show jsPDF object
console.log(window.PDFExport.isAvailable()); // Should return true
```

## File Size
- Minified: ~200KB
- Gzipped: ~60KB

## License
MIT License - Free for commercial use
