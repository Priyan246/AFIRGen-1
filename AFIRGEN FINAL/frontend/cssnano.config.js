module.exports = {
  preset: [
    'default',
    {
      discardComments: {
        removeAll: true,
      },
      normalizeWhitespace: true,
      colormin: true,
      minifyFontValues: true,
      minifyGradients: true,
      minifySelectors: true,
      mergeLonghand: true,
      mergeRules: true,
      reduceIdents: false, // Keep identifiers for debugging
      zindex: false, // Don't modify z-index values
    },
  ],
};
