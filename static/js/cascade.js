const regionSelect = document.getElementById("region");
const departementSelect = document.getElementById("departement");

if (regionSelect && departementSelect) {
    const urlParams = new URLSearchParams(window.location.search);
    const selectedDeptParameter = urlParams.get("departement_id") || "";

    const estFranceSelectionnee = () => {
        const option = regionSelect.selectedOptions[0];

        return option && (
            option.dataset.code === "99" ||
            option.dataset.libelle.toUpperCase() === "FRANCE"
        );
    };

    const chargerDepartements = async (isInitialLoad = false) => {
        const regionId = regionSelect.value;

        departementSelect.innerHTML = '<option value="">-- Choisir un département --</option>';
        departementSelect.disabled = false;
        departementSelect.required = true;

        if (estFranceSelectionnee()) {
            departementSelect.innerHTML = '<option value="">France entière</option>';
            departementSelect.disabled = true;
            departementSelect.required = false;
            return;
        }

        if (!regionId) {
            return;
        }

        try {
            const response = await fetch(`/api/departements/${regionId}`);
            const departements = await response.json();

            const optionTous = document.createElement("option");
            optionTous.value = "all";
            optionTous.textContent = "Tous les départements de la région";

            if (isInitialLoad && selectedDeptParameter === "all") {
                optionTous.selected = true;
            }
            departementSelect.appendChild(optionTous);

            for (const dept of departements) {
                const option = document.createElement("option");
                option.value = dept.id;
                option.textContent = `${dept.code} - ${dept.libelle}`;

                if (isInitialLoad && selectedDeptParameter && String(dept.id) === String(selectedDeptParameter)) {
                    option.selected = true;
                }
                departementSelect.appendChild(option);
            }
        } catch (error) {
            console.error("Erreur lors du chargement des départements :", error);
        }
    };

    regionSelect.addEventListener("change", () => chargerDepartements(false));
    chargerDepartements(true);
}