const regionSelect = document.getElementById("region");
const departementSelect = document.getElementById("departement");

if (regionSelect && departementSelect) {
    const estFranceSelectionnee = () => {
        const option = regionSelect.selectedOptions[0];

        return option && (
            option.dataset.code === "99" ||
            option.dataset.libelle.toUpperCase() === "FRANCE"
        );
    };

    const chargerDepartements = async () => {
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

            for (const dept of departements) {
                const option = document.createElement("option");
                option.value = dept.id;
                option.textContent = `${dept.code} - ${dept.libelle}`;
                departementSelect.appendChild(option);
            }
        } catch (error) {
            console.error("Erreur lors du chargement des départements :", error);
        }
    };

    regionSelect.addEventListener("change", chargerDepartements);
    chargerDepartements();
}
