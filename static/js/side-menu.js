const sideMenu = document.getElementById("sideMenu");
const menuToggle = document.getElementById("menuToggle");
const menuClose = document.getElementById("sideMenuClose");
const menuOverlay = document.getElementById("sideMenuOverlay");

function setMenu(open) {
    if (!sideMenu || !menuToggle || !menuOverlay) {
        return;
    }

    sideMenu.classList.toggle("is-open", open);
    menuToggle.classList.toggle("is-open", open);
    menuOverlay.classList.toggle("is-visible", open);
    document.body.classList.toggle("menu-open", open);
    sideMenu.setAttribute("aria-hidden", String(!open));
    menuToggle.setAttribute("aria-expanded", String(open));
    menuToggle.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
    open ? menuClose?.focus() : menuToggle.focus();
}

menuToggle?.addEventListener("click", () => setMenu(!sideMenu.classList.contains("is-open")));
menuClose?.addEventListener("click", () => setMenu(false));
menuOverlay?.addEventListener("click", () => setMenu(false));

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sideMenu?.classList.contains("is-open")) {
        setMenu(false);
    }
});
