document.addEventListener("DOMContentLoaded", () => {
    const loadingScreen = document.getElementById("loadingScreen");
    const loadingText = document.getElementById("loadingText");

    function afficherChargement(message = "Chargement des données...") {
        if (!loadingScreen) {
            console.error("Le bloc #loadingScreen est introuvable.");
            return;
        }

        if (loadingText) {
            loadingText.textContent = message;
        }

        loadingScreen.classList.add("loading-screen-visible");
        loadingScreen.setAttribute("aria-hidden", "false");
        document.body.classList.add("page-loading");
    }

    function masquerChargement() {
        if (!loadingScreen) {
            return;
        }

        loadingScreen.classList.remove("loading-screen-visible");
        loadingScreen.setAttribute("aria-hidden", "true");
        document.body.classList.remove("page-loading");
    }

    document.querySelectorAll("form").forEach(form => {
        form.addEventListener("submit", event => {
            if (!form.checkValidity()) {
                return;
            }

            event.preventDefault();

            afficherChargement("Chargement des données...");

            /*
             * Petit délai pour laisser le navigateur afficher le loader
             * avant d'envoyer réellement le formulaire.
             */
            setTimeout(() => {
                form.submit();
            }, 150);
        });
    });

    document.querySelectorAll("a[href]").forEach(lien => {
        lien.addEventListener("click", event => {
            const href = lien.getAttribute("href");

            if (
                !href ||
                href === "#" ||
                href.startsWith("#") ||
                lien.target === "_blank" ||
                event.ctrlKey ||
                event.shiftKey ||
                event.metaKey ||
                event.altKey
            ) {
                return;
            }

            const destination = new URL(lien.href, window.location.href);

            if (
                destination.pathname === window.location.pathname &&
                destination.search === window.location.search &&
                destination.hash
            ) {
                return;
            }

            event.preventDefault();

            afficherChargement("Chargement de la page...");

            setTimeout(() => {
                window.location.href = destination.href;
            }, 150);
        });
    });

    window.addEventListener("pageshow", masquerChargement);
    window.addEventListener("load", masquerChargement);
});