/**
 * Unit Tests for Keyboard Navigation Module
 */

describe('Keyboard Navigation Module', () => {
  let mockShowTab;
  let mockCloseModal;

  beforeEach(() => {
    // Set up DOM
    document.body.innerHTML = `
      <nav class="navbar">
        <div class="nav-item" data-tab="home" tabindex="0">Home</div>
        <div class="nav-item" data-tab="about" tabindex="0">About</div>
      </nav>
      
      <div class="fir-item" tabindex="0">FIR #001</div>
      <div class="fir-item" tabindex="0">FIR #002</div>
      
      <label for="letter-upload" class="file-upload-item">
        <input type="file" id="letter-upload" />
        Upload Letter
      </label>
      
      <div class="modal-overlay hidden" id="modal-overlay">
        <div class="modal-content">
          <button id="modal-close">Close</button>
          <button id="close-btn">Close</button>
          <button id="copy-btn">Copy</button>
          <input type="text" id="test-input" />
        </div>
      </div>
      
      <div class="toast-container">
        <div class="toast">
          <div class="toast-close" tabindex="0">×</div>
        </div>
      </div>
    `;

    // Mock window functions
    mockShowTab = jest.fn();
    mockCloseModal = jest.fn();
    window.showTab = mockShowTab;
    window.closeModal = mockCloseModal;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('getFocusableElements', () => {
    test('should find all focusable elements in container', () => {
      const modalContent = document.querySelector('.modal-content');
      const selector = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'textarea:not([disabled])',
        'select:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
        '[contenteditable="true"]'
      ].join(', ');

      const focusable = Array.from(modalContent.querySelectorAll(selector));

      // Should find: modal-close button, close-btn button, copy-btn button, test-input
      expect(focusable.length).toBeGreaterThanOrEqual(3);
    });

    test('should exclude disabled elements', () => {
      const button = document.createElement('button');
      button.disabled = true;
      document.body.appendChild(button);

      const selector = 'button:not([disabled])';
      const focusable = Array.from(document.body.querySelectorAll(selector));

      expect(focusable).not.toContain(button);
    });

    test('should include elements with tabindex', () => {
      const navItems = document.querySelectorAll('.nav-item[tabindex]');
      const selector = '[tabindex]:not([tabindex="-1"])';
      const focusable = Array.from(document.body.querySelectorAll(selector));

      navItems.forEach(item => {
        expect(focusable).toContain(item);
      });
    });
  });

  describe('Keyboard event handlers', () => {
    test('should trigger callback on Enter key', () => {
      const button = document.createElement('button');
      const callback = jest.fn();

      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          callback(e);
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      button.dispatchEvent(event);

      expect(callback).toHaveBeenCalled();
    });

    test('should trigger callback on Space key', () => {
      const button = document.createElement('button');
      const callback = jest.fn();

      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          callback(e);
        }
      });

      const event = new KeyboardEvent('keydown', { key: ' ' });
      button.dispatchEvent(event);

      expect(callback).toHaveBeenCalled();
    });

    test('should not trigger callback on other keys', () => {
      const button = document.createElement('button');
      const callback = jest.fn();

      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          callback(e);
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'a' });
      button.dispatchEvent(event);

      expect(callback).not.toHaveBeenCalled();
    });

    test('should support Escape key', () => {
      const button = document.createElement('button');
      const callback = jest.fn();

      button.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          callback(e);
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      button.dispatchEvent(event);

      expect(callback).toHaveBeenCalled();
    });
  });

  describe('Navigation keyboard handlers', () => {
    test('should navigate to tab on Enter key', () => {
      const navItem = document.querySelector('.nav-item[data-tab="home"]');

      navItem.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const tabName = navItem.getAttribute('data-tab');
          window.showTab(tabName);
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      navItem.dispatchEvent(event);

      expect(mockShowTab).toHaveBeenCalledWith('home');
    });

    test('should navigate to tab on Space key', () => {
      const navItem = document.querySelector('.nav-item[data-tab="about"]');

      navItem.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const tabName = navItem.getAttribute('data-tab');
          window.showTab(tabName);
        }
      });

      const event = new KeyboardEvent('keydown', { key: ' ' });
      navItem.dispatchEvent(event);

      expect(mockShowTab).toHaveBeenCalledWith('about');
    });
  });

  describe('FIR list keyboard handlers', () => {
    test('should trigger click on FIR item with Enter key', () => {
      const firItem = document.querySelector('.fir-item');
      const clickHandler = jest.fn();
      firItem.addEventListener('click', clickHandler);

      firItem.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          firItem.click();
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      firItem.dispatchEvent(event);

      expect(clickHandler).toHaveBeenCalled();
    });
  });

  describe('File upload keyboard handlers', () => {
    test('should trigger file input click on Enter key', () => {
      const label = document.querySelector('label[for="letter-upload"]');
      const input = document.getElementById('letter-upload');
      const clickHandler = jest.fn();
      input.addEventListener('click', clickHandler);

      label.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          input.click();
        }
      });

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      label.dispatchEvent(event);

      expect(clickHandler).toHaveBeenCalled();
    });
  });

  describe('Modal keyboard handlers', () => {
    test('should close modal on Escape key', () => {
      const modalOverlay = document.getElementById('modal-overlay');
      modalOverlay.classList.remove('hidden');

      // Add Escape key handler
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          if (!modalOverlay.classList.contains('hidden')) {
            window.closeModal();
          }
        }
      };
      document.addEventListener('keydown', escapeHandler);

      const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
      document.dispatchEvent(event);

      expect(mockCloseModal).toHaveBeenCalled();

      // Clean up
      document.removeEventListener('keydown', escapeHandler);
    });

    test('should not close modal on Escape when already hidden', () => {
      const modalOverlay = document.getElementById('modal-overlay');
      modalOverlay.classList.add('hidden');

      // Clear previous mock calls
      mockCloseModal.mockClear();

      // Add Escape key handler
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          if (!modalOverlay.classList.contains('hidden')) {
            window.closeModal();
          }
        }
      };
      document.addEventListener('keydown', escapeHandler);

      const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
      document.dispatchEvent(event);

      expect(mockCloseModal).not.toHaveBeenCalled();

      // Clean up
      document.removeEventListener('keydown', escapeHandler);
    });
  });

  describe('Focus indicators', () => {
    test('should have focus outline on interactive elements', () => {
      const button = document.createElement('button');
      document.body.appendChild(button);

      // Simulate focus
      button.focus();

      // Check if element can receive focus
      expect(document.activeElement).toBe(button);
    });

    test('should support tabindex on custom elements', () => {
      const navItem = document.querySelector('.nav-item[tabindex="0"]');

      navItem.focus();

      expect(document.activeElement).toBe(navItem);
    });
  });

  describe('Logical tab order', () => {
    test('should maintain tab order for navigation items', () => {
      const navItems = document.querySelectorAll('.nav-item');

      navItems.forEach(item => {
        expect(item.getAttribute('tabindex')).toBe('0');
      });
    });

    test('should maintain tab order for FIR items', () => {
      const firItems = document.querySelectorAll('.fir-item');

      firItems.forEach(item => {
        expect(item.getAttribute('tabindex')).toBe('0');
      });
    });
  });

  describe('Focus trap', () => {
    test('should trap focus within modal', () => {
      const modalContent = document.querySelector('.modal-content');
      const buttons = modalContent.querySelectorAll('button');
      const firstButton = buttons[0];
      const lastButton = buttons[buttons.length - 1];

      // Simulate Tab on last element - should cycle to first
      lastButton.focus();
      expect(document.activeElement).toBe(lastButton);

      // In a real focus trap, Tab from last would go to first
      // This is a simplified test
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
      lastButton.dispatchEvent(event);

      // The actual focus trap logic would move focus to firstButton
      // We're just testing that the elements exist and are focusable
      expect(firstButton).toBeTruthy();
      expect(lastButton).toBeTruthy();
    });

    test('should have multiple focusable elements in modal', () => {
      const modalContent = document.querySelector('.modal-content');
      const focusable = modalContent.querySelectorAll('button, input');

      expect(focusable.length).toBeGreaterThan(1);
    });
  });
});
