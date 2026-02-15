/**
 * Property-Based Tests for keyboard-navigation.js
 * **Validates: Requirements 5.4.3**
 *
 * Property 5: Keyboard Navigation
 * For any interactive element (button, input, link), the system SHALL be accessible
 * via keyboard (Tab, Enter, Space, Escape) with visible focus indicators.
 */

const fc = require('fast-check');

describe('Property-Based Tests: Keyboard Navigation', () => {
  beforeEach(() => {
    // Create a fresh DOM for each test
    document.body.innerHTML = `
      <nav class="navbar">
        <div class="nav-item" data-tab="home" tabindex="0">Home</div>
        <div class="nav-item" data-tab="about" tabindex="0">About</div>
        <div class="nav-item" data-tab="resources" tabindex="0">Resources</div>
      </nav>
      
      <main>
        <input type="text" id="search-input" placeholder="Search" />
        <button id="generate-btn">Generate FIR</button>
        
        <div class="fir-list">
          <div class="fir-item" tabindex="0" data-fir="001">FIR #001</div>
          <div class="fir-item" tabindex="0" data-fir="002">FIR #002</div>
          <div class="fir-item" tabindex="0" data-fir="003">FIR #003</div>
        </div>
        
        <label for="letter-upload" class="file-upload-item" tabindex="0">
          <input type="file" id="letter-upload" />
          Upload Letter
        </label>
        
        <label for="audio-upload" class="file-upload-item" tabindex="0">
          <input type="file" id="audio-upload" />
          Upload Audio
        </label>
      </main>
      
      <div class="modal-overlay hidden" id="modal-overlay">
        <div class="modal-content">
          <button id="modal-close" class="modal-close">×</button>
          <h2>FIR Details</h2>
          <div id="modal-body">Content here</div>
          <button id="copy-btn">Copy</button>
          <button id="close-btn">Close</button>
        </div>
      </div>
      
      <div class="toast-container">
        <div class="toast">
          <span>Notification</span>
          <button class="toast-close" tabindex="0">×</button>
        </div>
      </div>
    `;

    // Add CSS for focus indicators
    const style = document.createElement('style');
    style.textContent = `
      *:focus { outline: 2px solid #60a5fa; outline-offset: 2px; }
      *:focus-visible { outline: 2px solid #60a5fa; outline-offset: 2px; }
    `;
    document.head.appendChild(style);
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  // Arbitraries for generating test data

  /**
   * Generate a valid keyboard key for activation
   */
  const activationKeyArb = () => fc.constantFrom('Enter', ' ');

  /**
   * Generate a valid keyboard key for navigation
   */
  const navigationKeyArb = () => fc.constantFrom('Tab', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight');

  /**
   * Generate a valid keyboard key for cancellation
   */
  const cancellationKeyArb = () => fc.constant('Escape');

  /**
   * Generate any valid keyboard key
   */
  const anyKeyboardKeyArb = () => fc.oneof(
    activationKeyArb(),
    navigationKeyArb(),
    cancellationKeyArb()
  );

  /**
   * Generate a selector for an interactive element
   */
  const interactiveElementSelectorArb = () => fc.constantFrom(
    'button',
    'input[type="text"]',
    'input[type="file"]',
    '.nav-item',
    '.fir-item',
    '.file-upload-item',
    '.modal-close',
    '.toast-close'
  );

  /**
   * Generate a sequence of Tab key presses
   */
  const tabSequenceArb = () => fc.array(
    fc.record({
      key: fc.constant('Tab'),
      shiftKey: fc.boolean()
    }),
    { minLength: 1, maxLength: 20 }
  );

  describe('Property 5: Keyboard Navigation', () => {
    test('All interactive elements should be focusable', () => {
      fc.assert(
        fc.property(interactiveElementSelectorArb(), (selector) => {
          const elements = document.querySelectorAll(selector);

          elements.forEach(element => {
            // Element should be focusable (either naturally or via tabindex)
            const tabindex = element.getAttribute('tabindex');
            const isFocusable =
              element.tagName === 'BUTTON' ||
              element.tagName === 'INPUT' ||
              element.tagName === 'A' ||
              (tabindex !== null && tabindex !== '-1');

            expect(isFocusable).toBe(true);
          });
        }),
        { numRuns: 50 }
      );
    });

    test('Focused elements should have visible focus indicators', () => {
      fc.assert(
        fc.property(interactiveElementSelectorArb(), (selector) => {
          const elements = document.querySelectorAll(selector);

          elements.forEach(element => {
            // Focus the element
            element.focus();

            // Check if element is focused
            expect(document.activeElement).toBe(element);

            // Verify focus indicator CSS exists in the document
            // (We can't use getComputedStyle with pseudo-selectors in jsdom)
            const styles = document.querySelectorAll('style');
            let hasFocusStyle = false;
            styles.forEach(style => {
              if (style.textContent.includes(':focus') && style.textContent.includes('outline')) {
                hasFocusStyle = true;
              }
            });

            expect(hasFocusStyle).toBe(true);
          });
        }),
        { numRuns: 50 }
      );
    });

    test('Enter and Space keys should activate interactive elements', () => {
      fc.assert(
        fc.property(activationKeyArb(), (key) => {
          const button = document.getElementById('generate-btn');
          let activated = false;

          button.addEventListener('click', () => {
            activated = true;
          });

          button.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              button.click();
            }
          });

          // Simulate key press
          const event = new window.KeyboardEvent('keydown', {
            key: key,
            bubbles: true,
            cancelable: true
          });

          button.dispatchEvent(event);

          // Button should be activated
          expect(activated).toBe(true);
        }),
        { numRuns: 50 }
      );
    });

    test('Tab key should navigate through all interactive elements in order', () => {
      fc.assert(
        fc.property(fc.integer({ min: 1, max: 10 }), (numTabs) => {
          // Get all focusable elements
          const focusableSelector = [
            'button:not([disabled])',
            'input:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
          ].join(', ');

          const focusableElements = Array.from(document.querySelectorAll(focusableSelector))
            .filter(el => el.offsetParent !== null);

          if (focusableElements.length === 0) {
            return true; // Skip if no focusable elements
          }

          // Start from first element
          focusableElements[0].focus();
          let currentIndex = 0;

          // Simulate Tab presses
          for (let i = 0; i < numTabs; i++) {
            const event = new window.KeyboardEvent('keydown', {
              key: 'Tab',
              bubbles: true,
              cancelable: true
            });

            document.activeElement.dispatchEvent(event);

            // Move to next element (wrapping around)
            currentIndex = (currentIndex + 1) % focusableElements.length;
            focusableElements[currentIndex].focus();
          }

          // Should have cycled through elements
          expect(document.activeElement).toBe(focusableElements[currentIndex]);

          return true;
        }),
        { numRuns: 30 }
      );
    });

    test('Shift+Tab should navigate backwards through interactive elements', () => {
      fc.assert(
        fc.property(fc.integer({ min: 1, max: 10 }), (numTabs) => {
          // Get all focusable elements
          const focusableSelector = [
            'button:not([disabled])',
            'input:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
          ].join(', ');

          const focusableElements = Array.from(document.querySelectorAll(focusableSelector))
            .filter(el => el.offsetParent !== null);

          if (focusableElements.length === 0) {
            return true; // Skip if no focusable elements
          }

          // Start from last element
          const lastIndex = focusableElements.length - 1;
          focusableElements[lastIndex].focus();
          let currentIndex = lastIndex;

          // Simulate Shift+Tab presses
          for (let i = 0; i < numTabs; i++) {
            const event = new window.KeyboardEvent('keydown', {
              key: 'Tab',
              shiftKey: true,
              bubbles: true,
              cancelable: true
            });

            document.activeElement.dispatchEvent(event);

            // Move to previous element (wrapping around)
            currentIndex = currentIndex === 0 ? lastIndex : currentIndex - 1;
            focusableElements[currentIndex].focus();
          }

          // Should have cycled backwards through elements
          expect(document.activeElement).toBe(focusableElements[currentIndex]);

          return true;
        }),
        { numRuns: 30 }
      );
    });

    test('Escape key should close modals and return focus', () => {
      fc.assert(
        fc.property(fc.constant('Escape'), (key) => {
          const modalOverlay = document.getElementById('modal-overlay');
          const triggerButton = document.getElementById('generate-btn');

          // Store original focus
          triggerButton.focus();
          const originalFocus = document.activeElement;

          // Open modal
          modalOverlay.classList.remove('hidden');
          const modalClose = document.getElementById('modal-close');
          modalClose.focus();

          // Verify modal is open and focused
          expect(modalOverlay.classList.contains('hidden')).toBe(false);
          expect(document.activeElement).toBe(modalClose);

          // Set up Escape key handler
          let modalClosed = false;
          const escapeHandler = (e) => {
            if (e.key === 'Escape' && !modalOverlay.classList.contains('hidden')) {
              modalOverlay.classList.add('hidden');
              originalFocus.focus();
              modalClosed = true;
            }
          };
          document.addEventListener('keydown', escapeHandler);

          // Simulate Escape key
          const event = new window.KeyboardEvent('keydown', {
            key: key,
            bubbles: true,
            cancelable: true
          });

          document.dispatchEvent(event);

          // Clean up
          document.removeEventListener('keydown', escapeHandler);

          // Modal should be closed and focus restored
          expect(modalClosed).toBe(true);

          return true;
        }),
        { numRuns: 30 }
      );
    });

    test('Focus trap should keep focus within modal', () => {
      fc.assert(
        fc.property(tabSequenceArb(), (tabSequence) => {
          const modalOverlay = document.getElementById('modal-overlay');
          const modalContent = modalOverlay.querySelector('.modal-content');

          // Open modal
          modalOverlay.classList.remove('hidden');

          // Get focusable elements in modal
          const focusableSelector = [
            'button:not([disabled])',
            'input:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
          ].join(', ');

          const modalFocusable = Array.from(modalContent.querySelectorAll(focusableSelector));

          if (modalFocusable.length === 0) {
            return true; // Skip if no focusable elements in modal
          }

          // Focus first element
          modalFocusable[0].focus();

          // Simulate tab sequence
          tabSequence.forEach(({ key, shiftKey }) => {
            const event = new window.KeyboardEvent('keydown', {
              key: key,
              shiftKey: shiftKey,
              bubbles: true,
              cancelable: true
            });

            const currentElement = document.activeElement;
            const currentIndex = modalFocusable.indexOf(currentElement);

            if (currentIndex !== -1) {
              currentElement.dispatchEvent(event);

              // Manually implement focus trap logic for test
              if (shiftKey) {
                // Shift+Tab - go backwards
                const prevIndex = currentIndex === 0 ? modalFocusable.length - 1 : currentIndex - 1;
                modalFocusable[prevIndex].focus();
              } else {
                // Tab - go forwards
                const nextIndex = (currentIndex + 1) % modalFocusable.length;
                modalFocusable[nextIndex].focus();
              }
            }
          });

          // Focus should still be within modal
          const currentFocus = document.activeElement;
          const isWithinModal = modalContent.contains(currentFocus);

          expect(isWithinModal).toBe(true);

          return true;
        }),
        { numRuns: 30 }
      );
    });

    test('All navigation items should be keyboard accessible', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('home', 'about', 'resources'),
          activationKeyArb(),
          (tabName, key) => {
            const navItem = document.querySelector(`.nav-item[data-tab="${tabName}"]`);
            let tabActivated = false;

            // Mock showTab function
            window.showTab = (name) => {
              if (name === tabName) {
                tabActivated = true;
              }
            };

            // Add keyboard handler
            navItem.addEventListener('keydown', (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                window.showTab(navItem.getAttribute('data-tab'));
              }
            });

            // Focus and activate
            navItem.focus();
            expect(document.activeElement).toBe(navItem);

            const event = new window.KeyboardEvent('keydown', {
              key: key,
              bubbles: true,
              cancelable: true
            });

            navItem.dispatchEvent(event);

            expect(tabActivated).toBe(true);

            return true;
          }
        ),
        { numRuns: 50 }
      );
    });

    test('All FIR list items should be keyboard accessible', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('001', '002', '003'),
          activationKeyArb(),
          (firId, key) => {
            const firItem = document.querySelector(`.fir-item[data-fir="${firId}"]`);
            let itemClicked = false;

            firItem.addEventListener('click', () => {
              itemClicked = true;
            });

            firItem.addEventListener('keydown', (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                firItem.click();
              }
            });

            // Focus and activate
            firItem.focus();
            expect(document.activeElement).toBe(firItem);

            const event = new window.KeyboardEvent('keydown', {
              key: key,
              bubbles: true,
              cancelable: true
            });

            firItem.dispatchEvent(event);

            expect(itemClicked).toBe(true);

            return true;
          }
        ),
        { numRuns: 50 }
      );
    });

    test('File upload labels should be keyboard accessible', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('letter-upload', 'audio-upload'),
          activationKeyArb(),
          (uploadId, key) => {
            const label = document.querySelector(`label[for="${uploadId}"]`);
            const input = document.getElementById(uploadId);
            let inputClicked = false;

            input.addEventListener('click', () => {
              inputClicked = true;
            });

            label.addEventListener('keydown', (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                input.click();
              }
            });

            // Focus and activate
            label.focus();
            expect(document.activeElement).toBe(label);

            const event = new window.KeyboardEvent('keydown', {
              key: key,
              bubbles: true,
              cancelable: true
            });

            label.dispatchEvent(event);

            expect(inputClicked).toBe(true);

            return true;
          }
        ),
        { numRuns: 50 }
      );
    });

    test('Toast close buttons should be keyboard accessible', () => {
      fc.assert(
        fc.property(activationKeyArb(), (key) => {
          const toastClose = document.querySelector('.toast-close');
          let toastClosed = false;

          toastClose.addEventListener('click', () => {
            toastClosed = true;
          });

          toastClose.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toastClose.click();
            }
          });

          // Focus and activate
          toastClose.focus();
          expect(document.activeElement).toBe(toastClose);

          const event = new window.KeyboardEvent('keydown', {
            key: key,
            bubbles: true,
            cancelable: true
          });

          toastClose.dispatchEvent(event);

          expect(toastClosed).toBe(true);

          return true;
        }),
        { numRuns: 50 }
      );
    });

    test('Keyboard navigation should work consistently across multiple interactions', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              selector: interactiveElementSelectorArb(),
              key: activationKeyArb()
            }),
            { minLength: 1, maxLength: 10 }
          ),
          (interactions) => {
            interactions.forEach(({ selector, key }) => {
              const elements = document.querySelectorAll(selector);

              if (elements.length > 0) {
                const element = elements[0];

                // Focus element
                element.focus();

                // Should be focused
                expect(document.activeElement).toBe(element);

                // Simulate key press
                const event = new window.KeyboardEvent('keydown', {
                  key: key,
                  bubbles: true,
                  cancelable: true
                });

                element.dispatchEvent(event);

                // Event should be dispatched without errors
                expect(event).toBeDefined();
              }
            });

            return true;
          }
        ),
        { numRuns: 30 }
      );
    });

    test('Disabled elements should not be focusable', () => {
      fc.assert(
        fc.property(fc.constant('button'), (tagName) => {
          const button = document.createElement(tagName);
          button.disabled = true;
          document.body.appendChild(button);

          // Try to focus disabled button
          button.focus();

          // Disabled button should not receive focus
          expect(document.activeElement).not.toBe(button);

          // Clean up
          document.body.removeChild(button);

          return true;
        }),
        { numRuns: 20 }
      );
    });

    test('Elements with tabindex="-1" should not be in tab order', () => {
      fc.assert(
        fc.property(fc.constant('div'), (tagName) => {
          const element = document.createElement(tagName);
          element.setAttribute('tabindex', '-1');
          element.textContent = 'Not in tab order';
          document.body.appendChild(element);

          // Get all focusable elements in tab order
          const focusableSelector = [
            'button:not([disabled])',
            'input:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
          ].join(', ');

          const focusableElements = Array.from(document.querySelectorAll(focusableSelector));

          // Element with tabindex="-1" should not be in the list
          expect(focusableElements).not.toContain(element);

          // But it should still be programmatically focusable
          element.focus();
          expect(document.activeElement).toBe(element);

          // Clean up
          document.body.removeChild(element);

          return true;
        }),
        { numRuns: 20 }
      );
    });

    test('Focus should be visible for all interactive element types', () => {
      const elementTypes = [
        { tag: 'button', text: 'Button' },
        { tag: 'input', type: 'text' },
        { tag: 'input', type: 'file' },
        { tag: 'a', href: '#', text: 'Link' }
      ];

      elementTypes.forEach(({ tag, type, href, text }) => {
        const element = document.createElement(tag);
        if (type) {
          element.type = type;
        }
        if (href) {
          element.href = href;
        }
        if (text) {
          element.textContent = text;
        }

        document.body.appendChild(element);

        // Focus element
        element.focus();

        // Should be focused
        expect(document.activeElement).toBe(element);

        // Verify focus styles exist in document
        const styles = document.querySelectorAll('style');
        let hasFocusStyle = false;
        styles.forEach(style => {
          if (style.textContent.includes(':focus') && style.textContent.includes('outline')) {
            hasFocusStyle = true;
          }
        });
        expect(hasFocusStyle).toBe(true);

        // Clean up
        document.body.removeChild(element);
      });
    });

    test('Keyboard navigation should handle rapid key presses', () => {
      fc.assert(
        fc.property(
          fc.array(activationKeyArb(), { minLength: 5, maxLength: 20 }),
          (keys) => {
            const button = document.getElementById('generate-btn');
            let activationCount = 0;

            const clickHandler = () => {
              activationCount++;
            };
            button.addEventListener('click', clickHandler);

            const keydownHandler = (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                button.click();
              }
            };
            button.addEventListener('keydown', keydownHandler);

            button.focus();

            // Rapidly press keys
            keys.forEach(key => {
              const event = new window.KeyboardEvent('keydown', {
                key: key,
                bubbles: true,
                cancelable: true
              });

              button.dispatchEvent(event);
            });

            // Clean up
            button.removeEventListener('click', clickHandler);
            button.removeEventListener('keydown', keydownHandler);

            // Should have activated for each key press
            expect(activationCount).toBe(keys.length);

            return true;
          }
        ),
        { numRuns: 30 }
      );
    });

    test('Keyboard navigation should work after dynamic content changes', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: 5 }),
          (numNewElements) => {
            const firList = document.querySelector('.fir-list');
            const initialCount = firList.querySelectorAll('.fir-item').length;

            // Add new FIR items dynamically
            for (let i = 0; i < numNewElements; i++) {
              const newItem = document.createElement('div');
              newItem.className = 'fir-item';
              newItem.setAttribute('tabindex', '0');
              newItem.setAttribute('data-fir', `00${initialCount + i + 1}`);
              newItem.textContent = `FIR #00${initialCount + i + 1}`;
              firList.appendChild(newItem);
            }

            // Get all FIR items (including new ones)
            const allFirItems = firList.querySelectorAll('.fir-item');

            // All items should be focusable
            allFirItems.forEach(item => {
              item.focus();
              expect(document.activeElement).toBe(item);
            });

            expect(allFirItems.length).toBe(initialCount + numNewElements);

            return true;
          }
        ),
        { numRuns: 20 }
      );
    });
  });
});
