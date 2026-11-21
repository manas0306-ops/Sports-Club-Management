/**
 * The Champions Club - Ambient Interactive Audio & Tactile Physics Engine
 * Adds generative ambient lounge soundscapes, 3D card tilt physics, 
 * interactive floodlight rotary dial, and matchday protein shaker.
 */

// 1. Web Audio API Generative Synthesizer (Zero External MP3s Needed)
let audioCtx = null;
let isAudioPlaying = false;
let ambientInterval = null;

function initAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function playSoftClick() {
    try {
        initAudioContext();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(300, audioCtx.currentTime + 0.05);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.05);
    } catch (e) {}
}

function playHarmonicChord() {
    if (!isAudioPlaying || !audioCtx) return;
    const chords = [
        [220.00, 261.63, 329.63, 392.00], // A minor 7
        [174.61, 220.00, 261.63, 329.63], // F major 7
        [196.00, 246.94, 293.66, 392.00], // G major
        [164.81, 196.00, 246.94, 329.63]  // E minor 7
    ];
    const chord = chords[Math.floor(Math.random() * chords.length)];
    chord.forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime + i * 0.08);
        gain.gain.setValueAtTime(0.001, audioCtx.currentTime + i * 0.08);
        gain.gain.linearRampToValueAtTime(0.025, audioCtx.currentTime + i * 0.08 + 0.8);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + i * 0.08 + 3.8);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(audioCtx.currentTime + i * 0.08);
        osc.stop(audioCtx.currentTime + i * 0.08 + 4.0);
    });
}

function toggleAmbientLounge() {
    initAudioContext();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    isAudioPlaying = !isAudioPlaying;

    const bars = document.querySelectorAll('.sound-bar');
    const playBtnText = document.getElementById('ambient-btn-text');
    const playIcon = document.getElementById('ambient-play-icon');

    if (isAudioPlaying) {
        bars.forEach(b => b.classList.add('playing'));
        if (playBtnText) playBtnText.innerText = 'Sunset Lounge (Playing)';
        if (playIcon) playIcon.setAttribute('data-lucide', 'pause');
        playHarmonicChord();
        ambientInterval = setInterval(playHarmonicChord, 4200);
        if (window.showToast) showToast('Clubhouse Lounge Soundscape active 🎶');
    } else {
        bars.forEach(b => b.classList.remove('playing'));
        if (playBtnText) playBtnText.innerText = 'Club Ambient Vibe';
        if (playIcon) playIcon.setAttribute('data-lucide', 'play');
        clearInterval(ambientInterval);
        if (window.showToast) showToast('Soundscape paused');
    }
    if (window.lucide) lucide.createIcons();
}

// 2. Interactive 3D Holographic Card Physics
function setupHologramCards() {
    const cards = document.querySelectorAll('.hologram-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -12;
            const rotateY = ((x - centerX) / centerX) * 12;
            card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    });
}

// 3. Interactive Floodlight Rotary Arc Dial
function updateCourtFloodlights(value) {
    const val = parseInt(value);
    const dialProgress = document.getElementById('floodlight-dial-progress');
    const dialLabel = document.getElementById('floodlight-val-label');
    const courtVisual = document.getElementById('court-interactive-stage');
    const lampGlow = document.getElementById('halogen-lamp-glow');

    if (dialLabel) dialLabel.innerText = `${val}%`;

    // SVG arc stroke dashoffset (circumference = 2 * PI * 42 = 263.89)
    if (dialProgress) {
        const offset = 263.89 - (val / 100) * 263.89;
        dialProgress.style.strokeDashoffset = offset;
    }

    // Dynamic court lighting intensity
    if (courtVisual) {
        const brightness = 0.55 + (val / 100) * 0.75;
        const amberGlow = (val / 100) * 0.45;
        courtVisual.style.filter = `brightness(${brightness}) drop-shadow(0 0 ${val * 0.5}px rgba(251, 191, 36, ${amberGlow}))`;
    }

    if (lampGlow) {
        lampGlow.style.opacity = (val / 100).toString();
        lampGlow.style.transform = `scale(${0.8 + (val / 100) * 0.5})`;
    }
}

// 4. Interactive "Build Your Matchday Shake" Protein Shaker
let currentShakeMacros = {
    kcal: 220,
    protein: 15,
    carbs: 22,
    fats: 6,
    liquidPct: 35
};

const INGREDIENT_DATA = {
    'whey': { kcal: 130, protein: 26, carbs: 2, fats: 1, liquid: 20, color: '#f59e0b', name: 'Whey Isolate' },
    'banana': { kcal: 105, protein: 1, carbs: 27, fats: 0, liquid: 15, color: '#fef08a', name: 'Fresh Banana' },
    'peanut': { kcal: 190, protein: 8, carbs: 7, fats: 16, liquid: 12, color: '#b45309', name: 'Peanut Butter' },
    'espresso': { kcal: 5, protein: 0, carbs: 1, fats: 0, liquid: 10, color: '#451a03', name: 'Cold Brew Shot' },
    'chia': { kcal: 70, protein: 3, carbs: 6, fats: 4, liquid: 8, color: '#78350f', name: 'Chia Seeds' }
};

function addShakeIngredient(type) {
    playSoftClick();
    const ing = INGREDIENT_DATA[type];
    if (!ing) return;

    currentShakeMacros.kcal += ing.kcal;
    currentShakeMacros.protein += ing.protein;
    currentShakeMacros.carbs += ing.carbs;
    currentShakeMacros.fats += ing.fats;
    currentShakeMacros.liquidPct = Math.min(95, currentShakeMacros.liquidPct + ing.liquid);

    // Update liquid glass
    const liquid = document.getElementById('shake-liquid-fill');
    if (liquid) {
        liquid.style.height = `${currentShakeMacros.liquidPct}%`;
        liquid.style.background = `linear-gradient(180deg, ${ing.color} 0%, #d97706 100%)`;
    }

    // Update labels
    const kcalEl = document.getElementById('shake-kcal-val');
    const protEl = document.getElementById('shake-prot-val');
    const carbEl = document.getElementById('shake-carb-val');
    const fatEl = document.getElementById('shake-fat-val');

    if (kcalEl) kcalEl.innerText = `${currentShakeMacros.kcal} kcal`;
    if (protEl) protEl.innerText = `${currentShakeMacros.protein}g`;
    if (carbEl) carbEl.innerText = `${currentShakeMacros.carbs}g`;
    if (fatEl) fatEl.innerText = `${currentShakeMacros.fats}g`;

    showSparklesAtButton(event.target);
    if (window.showToast) showToast(`Added ${ing.name}! (+${ing.protein}g protein)`);
}

function resetShake() {
    playSoftClick();
    currentShakeMacros = { kcal: 220, protein: 15, carbs: 22, fats: 6, liquidPct: 35 };
    const liquid = document.getElementById('shake-liquid-fill');
    if (liquid) {
        liquid.style.height = '35%';
        liquid.style.background = 'linear-gradient(180deg, #f59e0b 0%, #d97706 100%)';
    }
    const kcalEl = document.getElementById('shake-kcal-val');
    const protEl = document.getElementById('shake-prot-val');
    const carbEl = document.getElementById('shake-carb-val');
    const fatEl = document.getElementById('shake-fat-val');
    if (kcalEl) kcalEl.innerText = '220 kcal';
    if (protEl) protEl.innerText = '15g';
    if (carbEl) carbEl.innerText = '22g';
    if (fatEl) fatEl.innerText = '6g';
    if (window.showToast) showToast('Shaker reset to base oat smoothie');
}

// 5. Confetti Sparkle Emitter
function showSparklesAtButton(element) {
    if (!element) return;
    const rect = element.getBoundingClientRect();
    for (let i = 0; i < 6; i++) {
        const sparkle = document.createElement('div');
        sparkle.className = 'fixed pointer-events-none z-50 text-amber-300 text-xs sparkle-badge';
        sparkle.innerHTML = ['✨', '⭐', '⚡', '💫'][Math.floor(Math.random() * 4)];
        sparkle.style.left = `${rect.left + rect.width / 2 + (Math.random() * 40 - 20)}px`;
        sparkle.style.top = `${rect.top + (Math.random() * 20 - 10)}px`;
        document.body.appendChild(sparkle);
        setTimeout(() => sparkle.remove(), 600);
    }
}

// 6. Interactive Court Surface Switcher
function selectCourtSurface(surface) {
    playSoftClick();
    const courtStage = document.getElementById('court-interactive-stage');
    const courtName = document.getElementById('active-court-name');
    const courtSurfaceType = document.getElementById('active-court-surface');
    const courtRate = document.getElementById('active-court-rate');

    document.querySelectorAll('.court-surface-pill').forEach(btn => {
        btn.classList.remove('glass-pill-active');
        btn.classList.add('glass-pill');
    });
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('glass-pill-active');
        event.currentTarget.classList.remove('glass-pill');
    }

    if (surface === 'clay') {
        if (courtStage) courtStage.style.background = 'linear-gradient(135deg, #b45309 0%, #78350f 50%, #9a3412 100%)';
        if (courtName) courtName.innerText = 'Centre Clay Tennis Court 1';
        if (courtSurfaceType) courtSurfaceType.innerText = 'Championship Red Clay (Rolled Daily)';
        if (courtRate) courtRate.innerText = '₹800 / hr';
    } else if (surface === 'cricket') {
        if (courtStage) courtStage.style.background = 'linear-gradient(135deg, #065f46 0%, #047857 50%, #064e3b 100%)';
        if (courtName) courtName.innerText = 'Floodlit Cricket Turf Net A';
        if (courtSurfaceType) courtSurfaceType.innerText = '22-Yard Astro Turf with Bowling Machine';
        if (courtRate) courtRate.innerText = '₹1,000 / hr';
    } else if (surface === 'padel') {
        if (courtStage) courtStage.style.background = 'linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #172554 100%)';
        if (courtName) courtName.innerText = 'Panoramic Glass Padel Court 1';
        if (courtSurfaceType) courtSurfaceType.innerText = 'Textured Blue Monofibre + 12mm Tempered Glass';
        if (courtRate) courtRate.innerText = '₹900 / hr';
    }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    setupHologramCards();
});
