/**
 * The Champions Club - Client Application Utilities (Warm Amber Glassmorphism UI)
 */

// Toast notification helper with Warm Frosted Glass styling
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    const isError = type === 'error';

    toast.className = `pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border backdrop-blur-2xl text-xs sm:text-sm font-semibold transition-all duration-300 transform translate-y-3 opacity-0 ${
        isSuccess ? 'bg-stone-900/90 text-emerald-300 border-emerald-500/40 shadow-emerald-500/15' :
        isError ? 'bg-stone-900/90 text-rose-300 border-rose-500/40 shadow-rose-500/15' :
        'bg-stone-900/90 text-amber-200 border-amber-500/40 shadow-amber-500/15'
    }`;

    const icon = isSuccess ? 'check-circle' : isError ? 'alert-circle' : 'info';
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 flex-shrink-0 ${isSuccess ? 'text-emerald-400' : isError ? 'text-rose-400' : 'text-amber-400'}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Smooth Entrance
    setTimeout(() => {
        toast.classList.remove('translate-y-3', 'opacity-0');
    }, 10);

    // Auto Dismiss
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-3');
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Modal open/close helpers
function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove('hidden');
        el.classList.add('flex');
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove('flex');
        el.classList.add('hidden');
    }
}

// Currency Formatter (INR)
function formatINR(val) {
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}
