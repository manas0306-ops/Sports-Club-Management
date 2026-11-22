const one = (q, el = document) => el.querySelector(q);
const all = (q, el = document) => Array.from(el.querySelectorAll(q));
const currency = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n / 100);
const localDay = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());

function notify(msg) {
  const box = one('#status');
  if (!box) return;
  box.textContent = msg;
  box.hidden = false;
  clearTimeout(box.timer);
  box.timer = setTimeout(() => { box.hidden = true; }, 6500);
}

// Global Form Submissions
document.addEventListener('submit', async e => {
  const form = e.target;
  const action = form.dataset.action;
  if (!action) return;
  e.preventDefault();

  const data = Object.fromEntries(new FormData(form));
  if (one('[data-cart]', form)) {
    data.cart = all('[data-sku]', form)
      .filter(i => Number(i.value) > 0)
      .map(i => ({ id: Number(i.dataset.sku), qty: Number(i.value) }));
  }

  if (action === 'book' && !data.start) {
    notify('Please select an available court slot from the schedule above.');
    return;
  }

  if (action === 'archive' && !confirm('Archive this account and terminate its active sessions?')) {
    return;
  }
  if (action === 'cancel' && !confirm('Are you sure you want to cancel this court reservation? A reversal refund receipt will be automatically generated.')) {
    return;
  }
  if (action === 'reject_payment' && !confirm('Are you sure you want to decline this payment approval and cancel the court booking?')) {
    return;
  }
  if (action === 'confirm_all_bookings' && !confirm('Are you sure you want to verify and confirm ALL pending court bookings and unverified payments?')) {
    return;
  }
  if (action === 'reject_all_bookings' && !confirm('Are you sure you want to reject ALL pending court bookings and unverified payments? Reserved court slots will be cancelled and released.')) {
    return;
  }
  if ((action === 'delete_product' || action === 'remove_product') && !confirm('Are you sure you want to permanently remove this product from the catalog?')) {
    return;
  }

  const btn = e.submitter;
  if (btn) btn.disabled = true;

  try {
    const r = await fetch('/api/' + action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Club-Request': '1' },
      body: JSON.stringify(data)
    });
    const v = await r.json();
    if (!r.ok) {
      throw Error(typeof v.detail === 'string' ? v.detail : 'Check the form inputs and try again.');
    }

    if (action === 'lead') {
      form.reset();
      notify('Inquiry received. The club concierge will reach out to you shortly.');
      return;
    }

    if (action === 'delete_product' || action === 'remove_product') {
      const row = form.closest('.line') || form.parentElement;
      if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        setTimeout(() => row.remove(), 300);
      }
      notify(v.message || 'Product removed from catalog.');
      return;
    }

    if (action === 'order') {
      const dept = data.department || 'Shop';
      sessionStorage.removeItem('club_cart_' + dept);
    }

    // Smooth In-Place Updates Without Full Page Reload
    if (action === 'reject_payment' || action === 'reject_booking') {
      const row = form.closest('.line') || form.parentElement;
      if (row) {
        const badge = row.querySelector('.pending-badge') || row.querySelector('.tag');
        if (badge) {
          badge.className = 'warn';
          badge.textContent = '✕ Rejected & Cancelled';
        }
        form.parentElement.innerHTML = '<span class="warn" style="font-size: 11px; padding: 4px 10px; border-radius: var(--radius-full);">✕ Rejected</span>';
      }
      notify(v.message || 'Payment approval rejected and court slot released.');
      return;
    }

    if (action === 'verify_payment' || action === 'approve_booking') {
      const row = form.closest('.line') || form.parentElement;
      if (row) {
        const badge = row.querySelector('.pending-badge') || row.querySelector('.warn');
        if (badge) {
          badge.className = 'verified-badge';
          badge.textContent = '✓ Verified by Staff';
        }
        form.parentElement.innerHTML = '<span class="verified-badge" style="font-size: 11px; padding: 4px 10px; border-radius: var(--radius-full);">✓ Verified</span>';
      }
      notify(v.message || 'Payment verified and court booking confirmed.');
      return;
    }

    if (action === 'confirm_all_bookings') {
      all('.pending-badge').forEach(badge => {
        badge.className = 'verified-badge';
        badge.textContent = '✓ Verified by Staff';
      });
      all('form[data-action="verify_payment"], form[data-action="approve_booking"], form[data-action="reject_payment"], form[data-action="reject_booking"]').forEach(f => {
        f.parentElement.innerHTML = '<span class="verified-badge" style="font-size: 11px; padding: 4px 10px; border-radius: var(--radius-full);">✓ Verified</span>';
      });
      notify(v.message || 'All pending bookings and payments have been verified and confirmed.');
      return;
    }

    if (action === 'reject_all_bookings') {
      all('.pending-badge').forEach(badge => {
        badge.className = 'warn';
        badge.textContent = '✕ Rejected & Cancelled';
      });
      all('form[data-action="verify_payment"], form[data-action="approve_booking"], form[data-action="reject_payment"], form[data-action="reject_booking"]').forEach(f => {
        f.parentElement.innerHTML = '<span class="warn" style="font-size: 11px; padding: 4px 10px; border-radius: var(--radius-full);">✕ Rejected</span>';
      });
      notify(v.message || 'All pending bookings and unverified payments have been rejected.');
      return;
    }

    if (action === 'cancel') {
      const row = form.closest('.line') || form.parentElement;
      if (row) {
        const badge = row.querySelector('.tag') || row.querySelector('.warn');
        if (badge) {
          badge.className = 'warn';
          badge.textContent = 'Cancelled & Refunded';
        }
        form.replaceWith(Object.assign(document.createElement('span'), {
          className: 'warn',
          style: 'font-size: 11px; padding: 4px 10px; border-radius: var(--radius-full);',
          textContent: 'Cancelled & Refunded'
        }));
      }
      notify(v.message || 'Court booking cancelled. Reversal refund receipt issued.');
      return;
    }

    if (v.redirect) {
      location.assign(v.redirect);
    } else if (v.receipt) {
      location.assign('/receipt/' + v.receipt);
    } else {
      sessionStorage.setItem('club-message', v.message || 'Changes saved successfully.');
      location.reload();
    }
  } catch (err) {
    notify(err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
});

// Demo Persona Quick-Fill
for (const button of all('[data-login]')) {
  button.onclick = () => {
    all('[data-login]').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    const emailField = one('form[data-action=login] [name=email]');
    const passField = one('form[data-action=login] [name=password]');
    if (emailField) emailField.value = button.dataset.login;
    if (passField) passField.value = 'password123';
  };
}

// Real-Time Cart Discount & Member Privilege Calculator
for (const cart of all('[data-cart]')) {
  const form = cart.closest('form');
  function estimate() {
    const tier = one('[data-member]', form)?.selectedOptions[0]?.dataset?.tier ||
                 one('input[data-tier]', form)?.dataset?.tier ||
                 document.body?.dataset?.tier ||
                 'Free';
    const pct = { Gold: 15, Silver: 10, Junior: 5, Free: 0 }[tier] || 0;
    let gross = 0;
    all('[data-sku]', cart).forEach(i => {
      gross += Number(i.value || 0) * Number(i.dataset.price || 0);
    });
    const discount = Math.round((gross * pct) / 100);
    const net = gross - discount;
    const estimateEl = one('[data-estimate]', cart);
    const qrBox = one('[data-cart-qr-box]', cart);
    const qrImg = one('[data-cart-qr]', cart);
    const dept = one('input[name="department"]', form)?.value || 'Shop';
    const submitBtn = one('button[type="submit"], button:not([type="button"])', form);

    if (estimateEl) {
      if (gross === 0) {
        estimateEl.textContent = 'Select item quantities above to calculate member pricing & savings.';
        if (qrBox) qrBox.style.display = 'none';
        if (submitBtn) submitBtn.textContent = 'Complete & Place Order';
      } else if (pct > 0) {
        estimateEl.innerHTML = `Subtotal: ${currency(gross)} &nbsp;·&nbsp; ` +
          `<span style="color: #059669; font-weight: 700;">${tier} ${pct}% Discount: −${currency(discount)}</span> &nbsp;·&nbsp; ` +
          `<strong style="color: var(--primary); font-size: 15px;">Net Total: ${currency(net)}</strong>`;
      } else {
        estimateEl.innerHTML = `<strong style="color: var(--primary); font-size: 15px;">Net Total: ${currency(net)}</strong> <span style="color: var(--slate-500); font-size: 12px;">(Standard pricing · 0% member discount)</span>`;
      }
    }

    if (gross > 0 && qrBox && qrImg) {
      const rupees = Math.round(net / 100);
      qrBox.style.display = 'block';
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(`upi://pay?pa=championsclub@icici&pn=The%20Champions%20Club&am=${rupees}&cu=INR&tn=${dept}-Order`)}`;
      if (form.elements.payment_ref) {
        form.elements.payment_ref.placeholder = `Enter 12-digit UPI UTR for ${currency(net)} payment`;
      }
      if (submitBtn) {
        submitBtn.textContent = `Submit ${dept} Order (${currency(net)}) →`;
      }
    } else if (qrBox) {
      qrBox.style.display = 'none';
    }
  }
  form.addEventListener('input', () => {
    estimate();
    const dept = one('input[name="department"]', form)?.value || 'Shop';
    const cartState = {};
    all('[data-sku]', cart).forEach(i => {
      if (Number(i.value) > 0) cartState[i.dataset.sku] = i.value;
    });
    sessionStorage.setItem('club_cart_' + dept, JSON.stringify(cartState));
  });
  form.addEventListener('change', estimate);

  // Restore persisted cart
  const dept = one('input[name="department"]', form)?.value || 'Shop';
  try {
    const saved = JSON.parse(sessionStorage.getItem('club_cart_' + dept) || '{}');
    let hasSaved = false;
    all('[data-sku]', cart).forEach(i => {
      if (saved[i.dataset.sku]) {
        i.value = saved[i.dataset.sku];
        hasSaved = true;
      }
    });
    if (hasSaved) estimate();
  } catch (e) {}

  estimate();
}

// Pro Shop Customer ID Lookup & Automatic Tier Discount Calculation
const shopMemberIdInput = one('#shop-member-id-input');
const shopMemberSelect = one('#shop-member-select');
const shopLookupBtn = one('#shop-lookup-btn');
const shopMemberName = one('#shop-member-name');
const shopMemberTierBadge = one('#shop-member-tier-badge');
const shopMemberDiscountBadge = one('#shop-member-discount-badge');

if (shopMemberSelect) {
  function updateShopMemberCard(opt) {
    const name = opt?.dataset.name || 'Walk-in Guest';
    const tier = opt?.dataset.tier || 'Free';
    const memId = opt?.value ? `#MEM-${opt.value}` : '';
    const uid = opt?.dataset.userId ? `#UID-${opt.dataset.userId}` : '';
    const pct = { Gold: 15, Silver: 10, Junior: 5, Free: 0 }[tier] || 0;

    if (shopMemberName) {
      shopMemberName.textContent = opt?.value ? `${name} (${memId} · ${uid})` : 'Walk-in Guest';
    }
    if (shopMemberTierBadge) {
      shopMemberTierBadge.className = tier === 'Gold' || tier === 'Silver' ? 'tag' : (tier === 'Junior' ? 'warn' : 'ghost');
      shopMemberTierBadge.textContent = `${tier} Subscription`;
    }
    if (shopMemberDiscountBadge) {
      if (pct > 0) {
        shopMemberDiscountBadge.innerHTML = `<span style="color: #059669; font-weight: 700;">★ ${pct}% Member Privilege Discount Active</span>`;
      } else {
        shopMemberDiscountBadge.textContent = 'Standard retail pricing (0% discount)';
      }
    }
    shopMemberSelect.dispatchEvent(new Event('input', { bubbles: true }));
    shopMemberSelect.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function lookupMemberById(val) {
    if (!val || !val.trim()) {
      shopMemberSelect.value = '';
      updateShopMemberCard(shopMemberSelect.selectedOptions[0]);
      return;
    }
    const cleanId = (val.match(/\d+/) || [])[0];
    if (!cleanId) return;

    const options = Array.from(shopMemberSelect.options);
    const match = options.find(o => o.value === cleanId || o.dataset.userId === cleanId);
    if (match) {
      shopMemberSelect.value = match.value;
      updateShopMemberCard(match);
      notify(`Matched: ${match.dataset.name} (${match.dataset.tier} tier)`);
    } else {
      notify(`No active member found matching ID "${val}".`);
    }
  }

  if (shopMemberIdInput) {
    shopMemberIdInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        lookupMemberById(shopMemberIdInput.value);
      }
    });
    shopMemberIdInput.addEventListener('input', () => {
      const clean = (shopMemberIdInput.value.match(/\d+/) || [])[0];
      if (clean) {
        const options = Array.from(shopMemberSelect.options);
        const match = options.find(o => o.value === clean || o.dataset.userId === clean);
        if (match) {
          shopMemberSelect.value = match.value;
          updateShopMemberCard(match);
        }
      } else if (!shopMemberIdInput.value.trim()) {
        shopMemberSelect.value = '';
        updateShopMemberCard(shopMemberSelect.selectedOptions[0]);
      }
    });
  }

  if (shopLookupBtn && shopMemberIdInput) {
    shopLookupBtn.addEventListener('click', () => {
      lookupMemberById(shopMemberIdInput.value);
    });
  }

  shopMemberSelect.addEventListener('change', () => {
    const selected = shopMemberSelect.selectedOptions[0];
    if (shopMemberIdInput) {
      shopMemberIdInput.value = selected?.value ? selected.value : '';
    }
    updateShopMemberCard(selected);
  });
}

// Live Directory Search (Front Desk)
const search = one('[data-search]');
if (search) {
  search.oninput = () => {
    const val = search.value.toLowerCase();
    all('[data-directory] p').forEach(p => {
      p.hidden = !p.textContent.toLowerCase().includes(val);
    });
  };
}

// Interactive Court Availability Board
for (const board of all('.board')) {
  const day = one('[data-day]', board);
  const week = one('[data-week]', board);
  const dest = one('[data-slots]', board);
  const form = one('form', board);
  day.value = localDay();
  let generation = 0;

  function choose(c, s, b) {
    if (!form) {
      location.assign('/login');
      return;
    }
    all('.slots .active', board).forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    form.elements.court_id.value = c.id;
    form.elements.start.value = s.start;
    form.dataset.base = c.price;
    form.dataset.kind = s.kind;
    form.dataset.label = `${c.name} (${c.kind}) · ${s.start.replace('T', ' · ')}`;
    quote();
  }

  function quote() {
    if (!form?.dataset.label) return;
    const profile = one('[data-member]', form)?.selectedOptions[0]?.dataset || document.body.dataset;
    const tier = profile.expiry && profile.expiry < form.elements.start.value.slice(0, 10)
      ? 'Free'
      : (profile.tier || 'Free');
    const pct = form.dataset.kind === 'Social'
      ? 100
      : ({ Gold: 100, Silver: 50, Junior: 30 }[tier] || 0);
    const gross = Number(form.dataset.base || 0);
    const calculated = gross * (100 - pct) / 100;
    const discount = gross - calculated;
    const chosenEl = one('[data-chosen]', form);
    if (chosenEl) {
      chosenEl.textContent = `${form.dataset.label} — Net: ${currency(calculated)} (${pct}% ${tier} benefit)`;
    }

    const billBox = one('[data-booking-bill]', form);
    const billItems = one('[data-bill-items]', form);
    const billTotal = one('[data-bill-total]', form);
    const qrBox = one('[data-bill-qr-box]', form);
    const qrImg = one('[data-bill-qr]', form);
    const submitBtn = one('button[type="submit"], button:not([type="button"])', form);

    if (billBox) {
      billBox.style.display = 'block';
      if (billItems) {
        billItems.innerHTML = `
          <div style="margin-bottom: 4px;"><b>Court Slot:</b> ${form.dataset.label}</div>
          <div style="margin-bottom: 4px;"><b>Standard Rate:</b> ${currency(gross)}</div>
          <div style="margin-bottom: 4px; color: #059669; font-weight: 600;">
            <b>${tier} Membership Benefit (${pct}%):</b> −${currency(discount)}
          </div>
        `;
      }
      if (billTotal) {
        billTotal.textContent = calculated > 0
          ? `Total Payable: ${currency(calculated)}`
          : `Total Payable: ₹0.00 (Included in ${tier} Tier)`;
      }

      if (calculated > 0 && qrBox && qrImg) {
        qrBox.style.display = 'flex';
        const rupees = Math.round(calculated / 100);
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(`upi://pay?pa=championsclub@icici&pn=The%20Champions%20Club&am=${rupees}&cu=INR&tn=Court-Booking`)}`;
        if (form.elements.payment_ref) {
          form.elements.payment_ref.required = true;
          form.elements.payment_ref.placeholder = `Enter 12-digit UPI UTR for ${currency(calculated)}`;
        }
        if (submitBtn) {
          submitBtn.textContent = `Submit Reservation & Payment UTR (${currency(calculated)})`;
        }
      } else {
        if (qrBox) qrBox.style.display = 'none';
        if (form.elements.payment_ref) {
          form.elements.payment_ref.required = false;
          form.elements.payment_ref.placeholder = 'No payment needed (Included in Membership)';
        }
        if (submitBtn) {
          submitBtn.textContent = 'Confirm Reservation (Complimentary)';
        }
      }
    }
  }

  if (form) form.addEventListener('change', quote);

  async function render() {
    const seq = ++generation;
    if (form) {
      form.elements.start.value = '';
      form.dataset.label = '';
      const chosenEl = one('[data-chosen]', form);
      if (chosenEl) chosenEl.textContent = 'Select an available time slot above.';
    }

    try {
      const query = new URLSearchParams({
        day: day.value,
        sport: one('[data-sport]', board).value,
        kind: one('[data-kind]', board).value
      });
      const r = await fetch('/api/availability?' + query);
      const rows = await r.json();
      if (seq !== generation) return;
      if (!r.ok) throw Error(rows.detail);

      dest.replaceChildren();

      for (const c of rows) {
        const row = document.createElement('div');
        row.className = 'slotrow';
        const title = document.createElement('strong');
        title.textContent = `${c.name} · ${c.kind}`;
        row.append(title);

        const times = document.createElement('div');
        times.className = 'slots';

        for (const s of c.slots) {
          const b = document.createElement('button');
          if (s.kind === 'Maintenance') {
            b.textContent = s.start.slice(11) + ' · 🛠️ Maint';
            b.disabled = true;
            b.style.background = '#fef3c7';
            b.style.color = '#92400e';
            b.style.borderColor = '#fcd34d';
            b.title = 'Court slot blocked for maintenance or tournament';
          } else {
            b.textContent = s.start.slice(11) + (s.kind === 'Social' ? ` · ${s.left}/8 spots` : '');
            b.disabled = !s.left;
            b.title = `${s.kind} session · ${s.left ? 'Available' : 'Unavailable'}`;
            b.onclick = () => choose(c, s, b);
          }
          times.append(b);
        }
        row.append(times);
        dest.append(row);
      }

      if (!rows.length) {
        dest.textContent = 'No courts match the selected filters for this date.';
      }

      all('button', week).forEach(b => {
        b.classList.toggle('active', b.dataset.date === day.value);
      });
    } catch (err) {
      dest.textContent = err.message;
    }
  }

  // Generate 7-Day Date Stepper
  const base = new Date(day.value + 'T12:00:00Z');
  for (let n = 0; n < 7; n++) {
    const t = new Date(base.getTime() + n * 86400000);
    const b = document.createElement('button');
    b.dataset.date = t.toISOString().slice(0, 10);
    const dayName = t.toLocaleDateString('en-GB', { weekday: 'short', timeZone: 'UTC' });
    const dayNum = t.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
    b.innerHTML = `<strong>${dayName}</strong><small>${dayNum}</small>`;
    b.onclick = () => {
      day.value = b.dataset.date;
      render();
    };
    week.append(b);
  }

  all('.filters input, .filters select', board).forEach(i => i.onchange = render);
  render();

  // Background Live Sync every 20 seconds
  setInterval(() => {
    if (!document.hidden && !form?.elements.start.value) {
      render();
    }
  }, 20000);
}

// Kitchen Order Queue (KOT) Live Sync every 10 seconds
const kitchen = one('#kitchen');
if (kitchen) {
  setInterval(async () => {
    if (document.hidden) return;
    try {
      const r = await fetch(location.href);
      if (!r.ok) return;
      const page = new DOMParser().parseFromString(await r.text(), 'text/html');
      const next = one('#kitchen', page);
      if (next) kitchen.replaceChildren(...next.childNodes);
    } catch {}
  }, 10000);
}

// Chart.js Executive Revenue Renderer
window.addEventListener('DOMContentLoaded', () => {
  window.lucide?.createIcons();
  const graph = one('#revenue');
  if (graph && window.Chart) {
    const vals = JSON.parse(graph.dataset.values);
    new Chart(graph, {
      type: 'bar',
      data: {
        labels: Object.keys(vals),
        datasets: [{
          label: 'Net Revenue (₹)',
          data: Object.values(vals).map(x => x / 100),
          backgroundColor: '#065f46',
          hoverBackgroundColor: '#047857',
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            titleFont: { size: 12, weight: 'bold' },
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              label: ctx => `Net Revenue: ₹${ctx.raw.toLocaleString('en-IN')}`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false }
          },
          y: {
            grid: { color: '#f1f5f9' },
            ticks: {
              callback: v => `₹${v.toLocaleString('en-IN')}`
            }
          }
        }
      }
    });
  }
});

// Session Messages & Alerts
const saved = sessionStorage.getItem('club-message');
if (saved) {
  notify(saved);
  sessionStorage.removeItem('club-message');
}
if (location.search.includes('registered=1')) {
  notify('Membership account created successfully. Please sign in with your email.');
}

// Physiotherapy Slot Picker
const physioDay = one('[data-physio-day]');
if (physioDay) {
  const form = physioDay.closest('form');
  const list = one('[data-physio-slots]', form);
  let request = 0;

  async function updatePhysio() {
    const version = ++request;
    list.replaceChildren();
    try {
      const q = new URLSearchParams({
        day: physioDay.value,
        staff_id: form.elements.staff_id.value
      });
      const response = await fetch('/api/physio/slots?' + q);
      const times = await response.json();
      if (version !== request) return;
      if (!response.ok) throw Error(times.detail);

      for (const t of times) {
        list.add(new Option(t.slice(11) + ' IST', t));
      }
      if (!times.length) {
        list.add(new Option('No slots available for selected date', ''));
      }
    } catch (error) {
      notify(error.message);
    }
  }

  form.elements.staff_id.onchange = updatePhysio;
  physioDay.onchange = updatePhysio;
  updatePhysio();
}

// Home Page Gear Catalog Filter & Search
const gearSearch = one('#gear-search');
const gearCatButtons = all('[data-gear-cat]');
const gearItems = all('.gear-item');

function filterGear() {
  const query = (gearSearch?.value || '').toLowerCase().trim();
  const activeCat = one('[data-gear-cat].active')?.dataset.gearCat || 'All';
  const inStockOnly = one('#gear-instock')?.checked || false;

  gearItems.forEach(card => {
    const name = (card.dataset.name || '').toLowerCase();
    const cat = card.dataset.category || '';
    const stock = Number(card.dataset.stock || 0);

    const matchesQuery = !query || name.includes(query);
    const matchesCat = activeCat === 'All' || cat === activeCat;
    const matchesStock = !inStockOnly || stock > 0;

    card.hidden = !(matchesQuery && matchesCat && matchesStock);
  });
}

if (gearSearch) gearSearch.addEventListener('input', filterGear);
const inStockCheckbox = one('#gear-instock');
if (inStockCheckbox) inStockCheckbox.addEventListener('change', filterGear);

gearCatButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    gearCatButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterGear();
  });
});

// Member Clubhouse Shop Filter & Search
const shopSearch = one('[data-shop-search]');
const shopCatButtons = all('[data-shop-cat]');
const shopRows = all('.shop-item-row');

function filterShopItems() {
  const query = (shopSearch?.value || '').toLowerCase().trim();
  const activeCat = one('[data-shop-cat].active')?.dataset.shopCat || 'All';

  shopRows.forEach(row => {
    const name = (row.dataset.name || '').toLowerCase();
    const cat = row.dataset.category || '';
    const matchesQuery = !query || name.includes(query);
    const matchesCat = activeCat === 'All' || cat === activeCat;
    row.hidden = !(matchesQuery && matchesCat);
  });
}

if (shopSearch) shopSearch.addEventListener('input', filterShopItems);
shopCatButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    shopCatButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterShopItems();
  });
});

// Cart Quantity Stepper Buttons
document.addEventListener('click', e => {
  const plusBtn = e.target.closest('[data-qty-plus]');
  const minusBtn = e.target.closest('[data-qty-minus]');
  if (plusBtn) {
    const input = plusBtn.parentElement.querySelector('input[data-sku]');
    if (input) {
      const max = Number(input.max || 999);
      const cur = Number(input.value || 0);
      if (cur < max) {
        input.value = cur + 1;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  } else if (minusBtn) {
    const input = minusBtn.parentElement.querySelector('input[data-sku]');
    if (input) {
      const min = Number(input.min || 0);
      const cur = Number(input.value || 0);
      if (cur > min) {
        input.value = cur - 1;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }
});

// Admin / Owner Account Directory Universal Search & Department Filtering
const adminSearch = one('#admin-user-search');
const memberTierPills = all('[data-member-tier]');
const staffRolePills = all('[data-staff-role]');

function filterAdminAccounts() {
  const query = (adminSearch?.value || '').toLowerCase().trim();
  const activeTier = one('[data-member-tier].active')?.dataset.memberTier || 'All';
  const activeRole = one('[data-staff-role].active')?.dataset.staffRole || 'All';

  // Filter Members List
  all('.admin-member-row').forEach(row => {
    const name = (row.dataset.name || '').toLowerCase();
    const email = (row.dataset.email || '').toLowerCase();
    const id = row.dataset.id || '';
    const memId = row.dataset.memId || '';
    const tier = row.dataset.tier || '';

    const textMatch = !query ||
      name.includes(query) ||
      email.includes(query) ||
      tier.toLowerCase().includes(query) ||
      id.includes(query) ||
      memId.includes(query) ||
      `#mem-${memId}`.toLowerCase().includes(query) ||
      `#uid-${id}`.toLowerCase().includes(query);

    const tierMatch = activeTier === 'All' || tier.toLowerCase() === activeTier.toLowerCase();

    row.hidden = !(textMatch && tierMatch);
  });

  // Filter Staff Directory
  all('.admin-staff-row').forEach(row => {
    const name = (row.dataset.name || '').toLowerCase();
    const email = (row.dataset.email || '').toLowerCase();
    const id = row.dataset.id || '';
    const role = row.dataset.role || '';

    const textMatch = !query ||
      name.includes(query) ||
      email.includes(query) ||
      role.toLowerCase().includes(query) ||
      id.includes(query) ||
      `#stf-${id}`.toLowerCase().includes(query);

    const roleMatch = activeRole === 'All' || role.toLowerCase() === activeRole.toLowerCase();

    row.hidden = !(textMatch && roleMatch);
  });
}

if (adminSearch) adminSearch.addEventListener('input', filterAdminAccounts);

memberTierPills.forEach(pill => {
  pill.addEventListener('click', () => {
    memberTierPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    filterAdminAccounts();
  });
});

staffRolePills.forEach(pill => {
  pill.addEventListener('click', () => {
    staffRolePills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    filterAdminAccounts();
  });
});


// Sidebar Module Navigation
function initSidebar() {
  const sidebarNav = document.getElementById('sidebar-nav');
  const main = document.getElementById('workspace-main');
  if (!sidebarNav || !main) return;

  // Select all modules, deduplicating by module id to prevent any collision
  const rawModules = Array.from(main.querySelectorAll('.club-module'));
  if (rawModules.length === 0) return;

  const seenIds = new Set();
  const modules = [];
  rawModules.forEach(m => {
    const id = m.dataset.module;
    if (id && !seenIds.has(id)) {
      seenIds.add(id);
      modules.push(m);
    }
  });

  sidebarNav.innerHTML = '';

  // Separate operational modules from the Profile module
  const opModules = modules.filter(m => m.dataset.module !== 'profile');
  const profileModule = modules.find(m => m.dataset.module === 'profile');

  // 1. All Modules Button
  const allBtn = document.createElement('button');
  allBtn.type = 'button';
  allBtn.className = 'sidebar-btn active';
  allBtn.dataset.target = 'all';
  allBtn.innerHTML = `<span><span class="sidebar-icon" style="margin-right: 8px;">✨</span> All Modules</span> <span class="sidebar-btn-badge" style="background: var(--slate-100); color: var(--slate-600);">${opModules.length}</span>`;
  sidebarNav.appendChild(allBtn);

  // 2. Individual Operational Module Buttons
  opModules.forEach(mod => {
    const id = mod.dataset.module;
    const title = mod.dataset.title || id;
    const icon = mod.dataset.icon || '📌';
    
    // Count pending badges
    const pendingCount = mod.querySelectorAll('.pending-badge').length;
    let badgeHtml = '';
    if (pendingCount > 0) {
      badgeHtml = `<span class="sidebar-btn-badge">⏳ ${pendingCount}</span>`;
    }

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sidebar-btn';
    btn.dataset.target = id;
    btn.innerHTML = `<span><span class="sidebar-icon" style="margin-right: 8px;">${icon}</span> ${title}</span> ${badgeHtml}`;
    sidebarNav.appendChild(btn);
  });

  // 3. Dedicated Profile Option in Sidebar
  if (profileModule) {
    const divider = document.createElement('div');
    divider.className = 'sidebar-divider';
    sidebarNav.appendChild(divider);

    const profBtn = document.createElement('button');
    profBtn.type = 'button';
    profBtn.className = 'sidebar-btn';
    profBtn.dataset.target = 'profile';
    profBtn.innerHTML = `<span><span class="sidebar-icon" style="margin-right: 8px;">👤</span> My Profile</span>`;
    sidebarNav.appendChild(profBtn);
  }

  function selectModule(target, updateUrl = true) {
    document.querySelectorAll('.sidebar-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.target === target);
    });

    if (target === 'all') {
      opModules.forEach(m => {
        m.style.display = 'block';
        m.style.opacity = '1';
        m.querySelectorAll('.club-module, section, details, .panel').forEach(c => {
          c.style.display = '';
        });
      });
      if (profileModule) {
        profileModule.style.display = 'none';
      }
      if (updateUrl) history.replaceState(null, null, ' ');
    } else if (target === 'profile') {
      opModules.forEach(m => {
        m.style.display = 'none';
      });
      if (profileModule) {
        profileModule.style.display = 'block';
        profileModule.style.opacity = '1';
        profileModule.querySelectorAll('section, details, .panel').forEach(c => c.style.display = '');
        profileModule.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      if (updateUrl) window.location.hash = 'profile';
    } else {
      // Find all elements with this module id (in case of aliases)
      const targetEls = main.querySelectorAll(`.club-module[data-module="${target}"]`);
      opModules.forEach(m => {
        if (m.dataset.module === target) {
          m.style.display = 'block';
          m.style.opacity = '1';
          m.querySelectorAll('section, details, .panel').forEach(c => {
            c.style.display = '';
          });
          // Also make sure if it was inside a details tag, it opens
          const parentDetails = m.closest('details');
          if (parentDetails) parentDetails.open = true;
          m.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          m.style.display = 'none';
        }
      });
      if (profileModule) {
        profileModule.style.display = 'none';
      }
      if (updateUrl) window.location.hash = target;
    }
  }

  // Sidebar button click handler
  document.addEventListener('click', e => {
    const btn = e.target.closest('.sidebar-btn');
    if (!btn || !btn.dataset.target) return;
    selectModule(btn.dataset.target, true);
  });

  // Check initial hash
  const initialHash = window.location.hash.slice(1);
  if (initialHash && modules.some(m => m.dataset.module === initialHash)) {
    selectModule(initialHash, false);
  } else {
    selectModule('all', false);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSidebar);
} else {
  initSidebar();
}


// Background Polling for Pending Approvals Count (Desk & Owner)
if (document.body.dataset.role === 'owner' || document.body.dataset.role === 'desk') {
  setInterval(async () => {
    try {
      const res = await fetch('/dashboard');
      if (!res.ok) return;
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const pendingCount = doc.querySelectorAll('.pending-badge').length;
      const btn = document.querySelector('.sidebar-btn[data-target="approvals"]');
      if (btn) {
        let badge = btn.querySelector('.sidebar-btn-badge');
        if (pendingCount > 0) {
          if (!badge) {
            badge = document.createElement('span');
            badge.className = 'sidebar-btn-badge';
            btn.appendChild(badge);
          }
          badge.textContent = `⏳ ${pendingCount}`;
        } else if (badge) {
          badge.remove();
        }
      }
    } catch (e) {}
  }, 45000);
}

// Real-Time Operational IST Clock & Date Synchronizer
function initOperationalClock() {
  function updateClock() {
    const clockEl = document.getElementById('operational-clock');
    const dateEl = document.getElementById('operational-date');
    if (!clockEl && !dateEl) return;

    const now = new Date();
    if (clockEl) {
      try {
        const timeStr = new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        }).format(now);
        clockEl.textContent = timeStr;
      } catch (err) {
        const hours = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        clockEl.textContent = `${hours}:${mins}`;
      }
    }

    if (dateEl) {
      try {
        const dateStr = new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Asia/Kolkata',
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        }).format(now);
        dateEl.textContent = dateStr;
      } catch (err) {}
    }
  }

  // Synchronize immediately
  updateClock();
  // Keep ticking live every 1 second
  setInterval(updateClock, 1000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initOperationalClock);
} else {
  initOperationalClock();
}

