/**
 * Jest Setup File
 * Adds polyfills and global configurations for tests
 */

// Add TextEncoder/TextDecoder polyfills for jsdom
const { TextEncoder, TextDecoder } = require('util');

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;
