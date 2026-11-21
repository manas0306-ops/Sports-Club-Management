/**
 * The Champions Club - Client Application Utilities
 */

// Toast notification helper
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    const isError = type === 'error';

    toast.className = `pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all duration-300 transform translate-y-2 opacity-0 ${
        isSuccess ? 'bg-emerald-50 text-emerald-900 border-emerald-200' :
        isError ? 'bg-rose-50 text-rose-900 border-rose-200' :
        'bg-slate-900 text-white border-slate-700'
    }`;

    const icon = isSuccess ? 'check-circle' : isError ? 'alert-circle' : 'info';
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 ${isSuccess ? 'text-emerald-600' : isError ? 'text-rose-600' : 'text-slate-400'}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Fade in
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Modal opener & closer
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

// Currency Formatter
function formatINR(val) {
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}
