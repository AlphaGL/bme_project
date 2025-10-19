// PWA Install Prompt Handler - Non-intrusive version
let deferredPrompt;
let installButton;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initializePWA();
});

function initializePWA() {
  // Create install button (initially hidden)
  createInstallButton();
  
  // Register service worker
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  }
  
  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] Install prompt available');
    e.preventDefault();
    deferredPrompt = e;
    
    // Show button after 10 seconds delay (non-intrusive)
    setTimeout(() => {
      showInstallButton();
    }, 10000);
  });
  
  // Listen for app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    hideInstallButton();
    deferredPrompt = null;
    
    // Show success message
    showToast('✅ App installed! You can now use FUTO BME offline.', 'success');
  });
  
  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches || 
      window.navigator.standalone === true) {
    console.log('[PWA] Running in standalone mode');
    hideInstallButton();
  }
}

async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/static/js/service-worker.js', {
      scope: '/'
    });
    
    console.log('[PWA] Service Worker registered:', registration.scope);
    
    // Check for updates periodically
    setInterval(() => {
      registration.update();
    }, 60 * 60 * 1000); // Check every hour
    
    // Listen for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New content available, show update prompt
          showUpdatePrompt();
        }
      });
    });
    
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function createInstallButton() {
  // Create the install button container
  const installContainer = document.createElement('div');
  installContainer.id = 'pwa-install-container';
  installContainer.style.cssText = `
    position: fixed;
    bottom: 100px;
    right: 20px;
    z-index: 9998;
    display: none;
  `;
  
  // Create the button
  installButton = document.createElement('button');
  installButton.id = 'pwa-install-btn';
  installButton.innerHTML = `
    <i class="fas fa-download me-2"></i>
    <span>Install App</span>
    <i class="fas fa-times ms-3 pwa-close-btn" style="opacity: 0.7; font-size: 0.9em;"></i>
  `;
  installButton.style.cssText = `
    background: linear-gradient(135deg, #8B1538 0%, #6B0F28 100%);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 6px 20px rgba(139, 21, 56, 0.5);
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
    animation: slideInUp 0.6s ease;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  `;
  
  // Add hover effect
  installButton.onmouseenter = () => {
    installButton.style.transform = 'translateY(-4px)';
    installButton.style.boxShadow = '0 8px 25px rgba(139, 21, 56, 0.6)';
  };
  
  installButton.onmouseleave = () => {
    installButton.style.transform = 'translateY(0)';
    installButton.style.boxShadow = '0 6px 20px rgba(139, 21, 56, 0.5)';
  };
  
  // Add click handlers
  installButton.addEventListener('click', (e) => {
    if (e.target.classList.contains('pwa-close-btn') || 
        e.target.closest('.pwa-close-btn')) {
      dismissInstallPrompt();
    } else {
      handleInstallClick();
    }
  });
  
  // Add animation styles
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(50px) scale(0.9);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
    
    @keyframes gentlePulse {
      0%, 100% {
        box-shadow: 0 6px 20px rgba(139, 21, 56, 0.5);
      }
      50% {
        box-shadow: 0 6px 25px rgba(139, 21, 56, 0.7);
      }
    }
    
    #pwa-install-btn {
      animation: slideInUp 0.6s ease, gentlePulse 3s infinite 5s;
    }
    
    .pwa-close-btn:hover {
      opacity: 1 !important;
      transform: scale(1.2);
    }
    
    @media (max-width: 768px) {
      #pwa-install-container {
        bottom: 90px !important;
        right: 15px !important;
      }
      
      #pwa-install-btn {
        font-size: 13px !important;
        padding: 12px 20px !important;
      }
      
      #pwa-install-btn span {
        display: none;
      }
      
      #pwa-install-btn::after {
        content: 'Install';
      }
    }
  `;
  document.head.appendChild(style);
  
  installContainer.appendChild(installButton);
  document.body.appendChild(installContainer);
}

function showInstallButton() {
  // Don't show if dismissed recently (within 7 days)
  const dismissedTime = localStorage.getItem('pwa-install-dismissed');
  if (dismissedTime) {
    const daysSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
    if (daysSinceDismissed < 7) {
      console.log('[PWA] Install prompt dismissed recently');
      return;
    }
  }
  
  // Don't show if already installed
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return;
  }
  
  const container = document.getElementById('pwa-install-container');
  if (container) {
    container.style.display = 'block';
  }
}

function hideInstallButton() {
  const container = document.getElementById('pwa-install-container');
  if (container) {
    container.style.display = 'none';
  }
}

function dismissInstallPrompt() {
  hideInstallButton();
  localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  showToast('💡 You can install the app anytime from your browser menu.', 'info');
}

async function handleInstallClick() {
  if (!deferredPrompt) {
    // Fallback: Show manual installation instructions
    showInstallInstructions();
    return;
  }
  
  // Hide the install button
  hideInstallButton();
  
  // Show the install prompt
  deferredPrompt.prompt();
  
  // Wait for the user's response
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`[PWA] User response: ${outcome}`);
  
  if (outcome === 'accepted') {
    console.log('[PWA] User accepted the install prompt');
    showToast('🎉 Installing FUTO BME app...', 'success');
  } else {
    console.log('[PWA] User dismissed the install prompt');
    // Show button again after 30 seconds if dismissed
    setTimeout(() => {
      if (!window.matchMedia('(display-mode: standalone)').matches) {
        showInstallButton();
      }
    }, 30000);
  }
  
  // Clear the deferredPrompt
  deferredPrompt = null;
}

function showInstallInstructions() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);
  
  let instructions = '';
  
  if (isIOS) {
    instructions = `
      <div style="text-align: left; padding: 10px;">
        <h5 class="mb-3"><i class="fab fa-apple me-2"></i>Install on iOS:</h5>
        <ol style="line-height: 2;">
          <li>Tap the <strong>Share</strong> button <i class="fas fa-share" style="color: #007AFF;"></i></li>
          <li>Scroll down and tap <strong>"Add to Home Screen"</strong> <i class="fas fa-plus-square" style="color: #007AFF;"></i></li>
          <li>Tap <strong>"Add"</strong> to confirm</li>
        </ol>
      </div>
    `;
  } else if (isAndroid) {
    instructions = `
      <div style="text-align: left; padding: 10px;">
        <h5 class="mb-3"><i class="fab fa-android me-2"></i>Install on Android:</h5>
        <ol style="line-height: 2;">
          <li>Tap the <strong>menu</strong> button <i class="fas fa-ellipsis-v"></i></li>
          <li>Tap <strong>"Install App"</strong> or <strong>"Add to Home Screen"</strong></li>
          <li>Tap <strong>"Install"</strong> to confirm</li>
        </ol>
      </div>
    `;
  } else {
    instructions = `
      <div style="text-align: left; padding: 10px;">
        <h5 class="mb-3"><i class="fas fa-desktop me-2"></i>Install on Desktop:</h5>
        <ol style="line-height: 2;">
          <li>Look for the <strong>install icon</strong> <i class="fas fa-download"></i> in the address bar</li>
          <li>Click it and select <strong>"Install"</strong></li>
          <li>Or use the browser menu: <strong>Settings → Install FUTO BME</strong></li>
        </ol>
      </div>
    `;
  }
  
  showModal('📱 Install FUTO BME App', instructions);
}

function showUpdatePrompt() {
  showToast('🔄 New version available! Please refresh to update.', 'warning', 15000, () => {
    window.location.reload();
  });
}

function showToast(message, type = 'success', duration = 5000, onAction = null) {
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} alert-dismissible fade show`;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    min-width: 300px;
    max-width: 400px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    animation: slideInRight 0.5s ease;
    border-radius: 10px;
    font-weight: 500;
  `;
  
  const actionButton = onAction ? `
    <button type="button" class="btn btn-sm btn-light ms-2" style="font-weight: 600;">
      Update Now
    </button>
  ` : '';
  
  toast.innerHTML = `
    ${message}
    ${actionButton}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  if (onAction) {
    const actionBtn = toast.querySelector('.btn-light');
    actionBtn.addEventListener('click', onAction);
  }
  
  document.body.appendChild(toast);
  
  // Auto remove after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 500);
  }, duration);
}

function showModal(title, content) {
  // Create modal backdrop
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop fade show';
  backdrop.style.zIndex = '9999';
  
  // Create modal
  const modal = document.createElement('div');
  modal.className = 'modal fade show';
  modal.style.display = 'block';
  modal.style.zIndex = '10000';
  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header" style="background: linear-gradient(135deg, #8B1538 0%, #6B0F28 100%); color: white;">
          <h5 class="modal-title">${title}</h5>
          <button type="button" class="btn-close btn-close-white close-pwa-modal"></button>
        </div>
        <div class="modal-body">
          ${content}
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary close-pwa-modal">Close</button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(backdrop);
  document.body.appendChild(modal);
  
  // Close modal handlers
  const closeButtons = modal.querySelectorAll('.close-pwa-modal');
  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modal.classList.remove('show');
      backdrop.classList.remove('show');
      setTimeout(() => {
        modal.remove();
        backdrop.remove();
      }, 300);
    });
  });
}

// Check for updates when page becomes visible
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && 'serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(registration => {
      registration.update();
    });
  }
});

// Add slideInRight animation
const animationStyle = document.createElement('style');
animationStyle.textContent = `
  @keyframes slideInRight {
    from {
      opacity: 0;
      transform: translateX(100px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
`;
document.head.appendChild(animationStyle);