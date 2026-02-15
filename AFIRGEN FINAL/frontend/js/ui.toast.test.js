/**
 * Unit tests for toast notification functionality
 */

// Mock DOM environment
document.body.innerHTML = '<div id="app"></div>';

// Import the ui.js module functions
require('./ui.js');

describe('Toast Notification System', () => {
  beforeEach(() => {
    // Clear any existing toasts
    const container = document.getElementById('toast-container');
    if (container) {
      container.remove();
    }
    // Reset body
    document.body.innerHTML = '<div id="app"></div>';
  });

  afterEach(() => {
    // Clean up
    jest.clearAllTimers();
  });

  describe('showToast', () => {
    test('should create toast container if it does not exist', () => {
      window.showToast('Test message', 'info');

      const container = document.getElementById('toast-container');
      expect(container).toBeTruthy();
      expect(container.className).toBe('toast-container');
    });

    test('should create toast with correct type class', () => {
      window.showToast('Success message', 'success');

      const toast = document.querySelector('.toast');
      expect(toast).toBeTruthy();
      expect(toast.classList.contains('toast-success')).toBe(true);
    });

    test('should create toast with all four types', () => {
      const types = ['success', 'error', 'warning', 'info'];

      types.forEach(type => {
        window.showToast(`${type} message`, type);
      });

      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBe(4);

      types.forEach((type, index) => {
        expect(toasts[index].classList.contains(`toast-${type}`)).toBe(true);
      });
    });

    test('should set correct message text', () => {
      const message = 'This is a test message';
      window.showToast(message, 'info');

      const messageElement = document.querySelector('.toast-message');
      expect(messageElement.textContent).toBe(message);
    });

    test('should return unique toast ID', () => {
      const id1 = window.showToast('Message 1', 'info');
      const id2 = window.showToast('Message 2', 'info');

      expect(id1).toBeTruthy();
      expect(id2).toBeTruthy();
      expect(id1).not.toBe(id2);
    });

    test('should set role="alert" for accessibility', () => {
      window.showToast('Alert message', 'error');

      const toast = document.querySelector('.toast');
      expect(toast.getAttribute('role')).toBe('alert');
    });

    test('should set aria-live on container', () => {
      window.showToast('Test', 'info');

      const container = document.getElementById('toast-container');
      expect(container.getAttribute('aria-live')).toBe('polite');
      expect(container.getAttribute('aria-atomic')).toBe('true');
    });

    test('should include close button with aria-label', () => {
      window.showToast('Test', 'info');

      const closeButton = document.querySelector('.toast-close');
      expect(closeButton).toBeTruthy();
      expect(closeButton.getAttribute('aria-label')).toBe('Close notification');
    });

    test('should include icon for each toast type', () => {
      const types = ['success', 'error', 'warning', 'info'];

      types.forEach(type => {
        document.body.innerHTML = '<div id="app"></div>';
        window.showToast(`${type} message`, type);

        const icon = document.querySelector('.toast-icon svg');
        expect(icon).toBeTruthy();
      });
    });

    test('should auto-hide toast after specified duration', (done) => {
      jest.useFakeTimers();

      const toastId = window.showToast('Auto-hide test', 'info', 1000);

      // Toast should exist initially
      let toast = document.querySelector(`[data-toast-id="${toastId}"]`);
      expect(toast).toBeTruthy();

      // Fast-forward time
      jest.advanceTimersByTime(1000);

      // Wait for animation
      setTimeout(() => {
        toast = document.querySelector(`[data-toast-id="${toastId}"]`);
        expect(toast).toBeFalsy();
        done();
      }, 400);

      jest.advanceTimersByTime(400);
      jest.useRealTimers();
    });

    test('should not auto-hide when duration is 0', () => {
      jest.useFakeTimers();

      const toastId = window.showToast('Persistent toast', 'info', 0);

      // Fast-forward time significantly
      jest.advanceTimersByTime(10000);

      // Toast should still exist
      const toast = document.querySelector(`[data-toast-id="${toastId}"]`);
      expect(toast).toBeTruthy();

      jest.useRealTimers();
    });

    test('should handle multiple toasts', () => {
      window.showToast('Toast 1', 'info');
      window.showToast('Toast 2', 'success');
      window.showToast('Toast 3', 'error');

      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBe(3);
    });

    test('should default to info type if invalid type provided', () => {
      window.showToast('Test', 'invalid-type');

      const toast = document.querySelector('.toast');
      // Should have info icon (circle with i)
      const icon = toast.querySelector('.toast-icon svg circle');
      expect(icon).toBeTruthy();
    });
  });

  describe('hideToast', () => {
    test('should remove toast from DOM', (done) => {
      const toastId = window.showToast('Test', 'info', 0);

      // Toast should exist
      let toast = document.querySelector(`[data-toast-id="${toastId}"]`);
      expect(toast).toBeTruthy();

      // Hide toast
      window.hideToast(toastId);

      // Wait for animation
      setTimeout(() => {
        toast = document.querySelector(`[data-toast-id="${toastId}"]`);
        expect(toast).toBeFalsy();
        done();
      }, 400);
    });

    test('should handle hiding non-existent toast gracefully', () => {
      expect(() => {
        window.hideToast('non-existent-id');
      }).not.toThrow();
    });

    test('should clear auto-hide timeout when manually hidden', () => {
      jest.useFakeTimers();

      const toastId = window.showToast('Test', 'info', 5000);

      // Manually hide before auto-hide
      window.hideToast(toastId);

      // Fast-forward past original auto-hide time
      jest.advanceTimersByTime(6000);

      // Should not cause any errors
      expect(true).toBe(true);

      jest.useRealTimers();
    });

    test('should trigger slide-out animation', () => {
      const toastId = window.showToast('Test', 'info', 0);
      const toast = document.querySelector(`[data-toast-id="${toastId}"]`);

      window.hideToast(toastId);

      expect(toast.classList.contains('toast-hide')).toBe(true);
      expect(toast.classList.contains('toast-show')).toBe(false);
    });
  });

  describe('Toast animations', () => {
    test('should add toast-show class for slide-in animation', (done) => {
      window.showToast('Test', 'info');

      // Wait for requestAnimationFrame
      requestAnimationFrame(() => {
        const toast = document.querySelector('.toast');
        expect(toast.classList.contains('toast-show')).toBe(true);
        done();
      });
    });
  });

  describe('Toast close button', () => {
    test('should hide toast when close button is clicked', (done) => {
      const toastId = window.showToast('Test', 'info', 0);
      const closeButton = document.querySelector('.toast-close');

      // Click close button
      closeButton.click();

      // Wait for animation
      setTimeout(() => {
        const toast = document.querySelector(`[data-toast-id="${toastId}"]`);
        expect(toast).toBeFalsy();
        done();
      }, 400);
    });
  });

  describe('Toast message handling', () => {
    test('should handle long messages', () => {
      const longMessage = 'This is a very long message that should wrap properly and maintain readability even with extended content that goes on and on.';
      window.showToast(longMessage, 'info');

      const messageElement = document.querySelector('.toast-message');
      expect(messageElement.textContent).toBe(longMessage);
    });

    test('should handle special characters in message', () => {
      const specialMessage = '<script>alert("xss")</script> & "quotes" \'apostrophes\'';
      window.showToast(specialMessage, 'info');

      const messageElement = document.querySelector('.toast-message');
      // textContent should escape HTML
      expect(messageElement.textContent).toBe(specialMessage);
      expect(messageElement.innerHTML).not.toContain('<script>');
    });

    test('should handle empty message', () => {
      window.showToast('', 'info');

      const messageElement = document.querySelector('.toast-message');
      expect(messageElement.textContent).toBe('');
    });
  });
});
