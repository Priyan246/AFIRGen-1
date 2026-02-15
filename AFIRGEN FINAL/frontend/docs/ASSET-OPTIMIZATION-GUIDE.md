# Asset Optimization Guide

## Overview

This document provides guidelines for optimizing assets (images, fonts, and other resources) in the AFIRGen frontend application to ensure optimal performance.

## Current State

### Images
- **Status**: No raster images currently used
- **Implementation**: All icons are inline SVG (optimal for performance)
- **Recommendation**: Continue using SVG for icons and illustrations

### Fonts
- **Current**: Google Fonts (Inter family)
- **Optimization**: Implemented preconnect and dns-prefetch
- **Font Display**: Using `font-display: swap` for better perceived performance

### Resource Hints
- ✅ Preconnect to fonts.googleapis.com
- ✅ Preconnect to fonts.gstatic.com (with crossorigin)
- ✅ DNS-prefetch for font domains

## Image Optimization Guidelines

### When Adding Images

If you need to add raster images in the future, follow these guidelines:

#### 1. Format Selection
- **WebP**: Primary format (85% quality, ~30% smaller than JPEG)
- **JPEG**: Fallback for older browsers
- **PNG**: Only for images requiring transparency
- **SVG**: Preferred for icons, logos, and illustrations

#### 2. Compression
```bash
# Convert to WebP (requires cwebp tool)
cwebp -q 85 input.jpg -o output.webp

# Optimize JPEG (requires jpegoptim)
jpegoptim --max=85 --strip-all input.jpg

# Optimize PNG (requires optipng)
optipng -o7 input.png
```

#### 3. Responsive Images
Use `srcset` for different screen sizes:

```html
<img 
  src="image-800w.webp" 
  srcset="image-400w.webp 400w,
          image-800w.webp 800w,
          image-1200w.webp 1200w"
  sizes="(max-width: 600px) 400px,
         (max-width: 1200px) 800px,
         1200px"
  alt="Description"
  loading="lazy"
  decoding="async"
>
```

#### 4. Lazy Loading
Add `loading="lazy"` to all images below the fold:

```html
<img src="image.webp" alt="Description" loading="lazy">
```

#### 5. Image Dimensions
Always specify width and height to prevent layout shift:

```html
<img src="image.webp" alt="Description" width="800" height="600" loading="lazy">
```

### WebP with Fallback

Use `<picture>` element for WebP with JPEG/PNG fallback:

```html
<picture>
  <source srcset="image.webp" type="image/webp">
  <source srcset="image.jpg" type="image/jpeg">
  <img src="image.jpg" alt="Description" loading="lazy">
</picture>
```

## Font Optimization

### Current Implementation

The application uses Google Fonts with the following optimizations:

1. **Preconnect**: Establishes early connection to font servers
2. **DNS-prefetch**: Resolves DNS early for faster font loading
3. **font-display: swap**: Shows fallback font immediately, swaps when custom font loads

### Font Loading Strategy

```html
<!-- Resource hints -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="dns-prefetch" href="https://fonts.googleapis.com">
<link rel="dns-prefetch" href="https://fonts.gstatic.com">

<!-- Font with display=swap -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
```

### System Font Fallback

The CSS includes a comprehensive system font stack:

```css
font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

This ensures:
- Fast initial render with system fonts
- Smooth transition when Inter loads
- Graceful degradation if font fails to load

### Font Subsetting (Future Optimization)

If you need to reduce font file size further:

1. **Use Google Fonts API with text parameter**:
```
https://fonts.googleapis.com/css2?family=Inter:wght@400;700&text=YourSpecificCharacters
```

2. **Self-host with subset**:
```bash
# Install pyftsubset (part of fonttools)
pip install fonttools

# Create subset
pyftsubset Inter-Regular.ttf \
  --output-file=Inter-Regular-subset.woff2 \
  --flavor=woff2 \
  --layout-features=* \
  --unicodes=U+0020-007E,U+00A0-00FF
```

## Resource Hints

### Implemented

```html
<!-- Preconnect: Establish early connection -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- DNS-prefetch: Resolve DNS early -->
<link rel="dns-prefetch" href="https://fonts.googleapis.com">
<link rel="dns-prefetch" href="https://fonts.gstatic.com">
```

### Future Additions

When API domain is known, add:

```html
<!-- Preconnect to API -->
<link rel="preconnect" href="https://api.afirgen.example.com">
<link rel="dns-prefetch" href="https://api.afirgen.example.com">
```

For critical resources:

```html
<!-- Prefetch next page resources -->
<link rel="prefetch" href="/about.html">

<!-- Preload critical resources -->
<link rel="preload" href="css/main.css" as="style">
<link rel="preload" href="js/app.js" as="script">
```

## SVG Optimization

### Current State
All icons are inline SVG, which is optimal for:
- No additional HTTP requests
- CSS styling and animations
- Accessibility (can add aria-labels)
- Small file size

### SVG Optimization Tools

If adding external SVG files:

```bash
# Install SVGO
npm install -g svgo

# Optimize SVG
svgo input.svg -o output.svg

# Batch optimize
svgo -f ./assets/icons -o ./assets/icons-optimized
```

### Inline SVG Best Practices

```html
<!-- Add aria-hidden for decorative icons -->
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24">
  <path d="..."/>
</svg>

<!-- Add title for meaningful icons -->
<svg role="img" aria-labelledby="icon-title" width="24" height="24" viewBox="0 0 24 24">
  <title id="icon-title">Search</title>
  <path d="..."/>
</svg>
```

## Performance Metrics

### Target Metrics
- **Total bundle size**: <500KB (gzipped)
- **Image size**: <100KB per image (WebP)
- **Font size**: <50KB per weight
- **First Contentful Paint**: <1s
- **Largest Contentful Paint**: <2.5s

### Measuring Performance

```bash
# Check file sizes
npm run verify:sizes

# Lighthouse audit
npx lighthouse http://localhost:3000 --view

# WebPageTest
# Visit https://www.webpagetest.org/
```

## Build Process Integration

### Current Build Scripts

```json
{
  "build:css": "cssnano css/main.css dist/css/main.min.css",
  "build:js": "terser js/app.js -o dist/js/app.min.js",
  "build:html": "html-minifier -o dist/index.html index.html"
}
```

### Future: Image Optimization Script

Create `scripts/optimize-images.js`:

```javascript
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function optimizeImage(inputPath, outputDir) {
  const filename = path.basename(inputPath, path.extname(inputPath));
  
  // Generate WebP
  await sharp(inputPath)
    .webp({ quality: 85 })
    .toFile(path.join(outputDir, `${filename}.webp`));
  
  // Generate optimized JPEG fallback
  await sharp(inputPath)
    .jpeg({ quality: 85, progressive: true })
    .toFile(path.join(outputDir, `${filename}.jpg`));
  
  console.log(`Optimized: ${filename}`);
}

// Usage: node scripts/optimize-images.js
```

Add to package.json:

```json
{
  "scripts": {
    "optimize:images": "node scripts/optimize-images.js"
  },
  "devDependencies": {
    "sharp": "^0.32.0"
  }
}
```

## Checklist

### Images
- [ ] Convert to WebP format (quality 85)
- [ ] Provide JPEG/PNG fallback
- [ ] Add lazy loading (`loading="lazy"`)
- [ ] Use responsive images (`srcset`)
- [ ] Specify dimensions (width/height)
- [ ] Optimize with compression tools
- [ ] Use SVG for icons and logos

### Fonts
- [x] Preconnect to font domains
- [x] DNS-prefetch for font domains
- [x] Use `font-display: swap`
- [x] System font fallback stack
- [ ] Consider font subsetting (if needed)
- [ ] Self-host fonts (optional)

### Resource Hints
- [x] Preconnect to font servers
- [x] DNS-prefetch for fonts
- [ ] Preconnect to API domain (when known)
- [ ] Prefetch next page resources
- [ ] Preload critical resources

### Performance
- [x] Minify CSS
- [x] Minify JavaScript
- [x] Minify HTML
- [x] Gzip compression (via nginx)
- [ ] Brotli compression (optional)
- [ ] CDN for static assets (optional)

## Tools and Resources

### Image Optimization
- **cwebp**: WebP converter (https://developers.google.com/speed/webp/download)
- **sharp**: Node.js image processing (https://sharp.pixelplumbing.com/)
- **Squoosh**: Online image optimizer (https://squoosh.app/)
- **ImageOptim**: Mac app for image optimization

### Font Optimization
- **Google Fonts**: Optimized font delivery
- **Font Squirrel**: Font subsetting tool
- **fonttools**: Python font manipulation library

### Performance Testing
- **Lighthouse**: Chrome DevTools
- **WebPageTest**: https://www.webpagetest.org/
- **GTmetrix**: https://gtmetrix.com/

## References

- [Web.dev Image Optimization](https://web.dev/fast/#optimize-your-images)
- [Web.dev Font Optimization](https://web.dev/font-best-practices/)
- [MDN Lazy Loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading)
- [Google Fonts Best Practices](https://csswizardry.com/2020/05/the-fastest-google-fonts/)
