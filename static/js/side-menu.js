const mainHeader = document.getElementById("mainHeader");
const sideMenu = document.getElementById("sideMenu");

function updateSideMenu() {
    if (!mainHeader || !sideMenu) {
        return;
    }

    const headerBottom = mainHeader.getBoundingClientRect().bottom;

    if (headerBottom < 0) {
        sideMenu.classList.add("side-menu-visible");
    } else {
        sideMenu.classList.remove("side-menu-visible");
    }
}

window.addEventListener("scroll", updateSideMenu);
window.addEventListener("resize", updateSideMenu);
updateSideMenu();