function startFormattedCountdown() {
    const countdownEl = document.getElementById("countdown");
    const targetDateStr = countdownEl.dataset.target; // viene del atributo data-target
    const countdownDate = new Date(targetDateStr).getTime();

    const timer = setInterval(() => {
        const now = new Date().getTime();
        const distance = countdownDate - now;

        if (distance <= 0) {
            clearInterval(timer);
            countdownEl.textContent = "Lights out!";
            countdownEl.style.color = "var(--f1-red)";
            const actionsDiv = document.querySelector(".actions");
            if (actionsDiv) actionsDiv.innerHTML = '';
            return;
        }

        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        countdownEl.textContent = 
            `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }, 1000);
}

// Iniciar el countdown cuando cargue la página
window.addEventListener("DOMContentLoaded", startFormattedCountdown);