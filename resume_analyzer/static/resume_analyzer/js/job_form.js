document.addEventListener("DOMContentLoaded", function () {
    /* -----------------------------
       SCORE WEIGHT
    ------------------------------ */

    const slider = document.getElementById("sw");
    const skillLabel = document.getElementById("sw-label");
    const similarityLabel = document.getElementById("sim-label");

    function updateWeights() {
        if (!slider) return;

        const skill = Number(slider.value || 70);
        const similarity = 100 - skill;

        if (skillLabel) {
            skillLabel.textContent = `${skill}%`;
        }

        if (similarityLabel) {
            similarityLabel.textContent = `${similarity}%`;
        }
    }

    if (slider) {
        slider.addEventListener("input", updateWeights);
        updateWeights();
    }


    /* -----------------------------
       SKILL CHIPS
    ------------------------------ */

    function setupSkillBox(boxId, inputId, hiddenId, type) {
        const box = document.getElementById(boxId);
        const input = document.getElementById(inputId);
        const hidden = document.getElementById(hiddenId);

        if (!box || !input || !hidden) return;

        let skills = [];

        function loadInitialSkills() {
            const value = hidden.value.trim();

            if (!value) return;

            try {
                const parsed = JSON.parse(value);

                if (Array.isArray(parsed)) {
                    skills = parsed;
                    return;
                }
            } catch (error) {
                // Existing form values may be comma-separated.
            }

            skills = value
                .split(",")
                .map(skill => skill.trim())
                .filter(Boolean);
        }

        function syncHidden() {
            hidden.value = skills.join(",");
        }

        function render() {
            box.querySelectorAll(".skill-chip").forEach(chip => chip.remove());

            skills.forEach((skill, index) => {
                const chip = document.createElement("span");

                chip.className =
                    type === "required"
                        ? "skill-chip inline-flex items-center gap-1.5 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700"
                        : "skill-chip inline-flex items-center gap-1.5 rounded-full border border-purple-100 bg-purple-50 px-3 py-1.5 text-xs font-medium text-purple-700";

                const icon = document.createElement("span");
                icon.textContent = type === "required" ? "✓" : "+";

                const text = document.createElement("span");
                text.textContent = skill;

                const removeButton = document.createElement("button");
                removeButton.type = "button";
                removeButton.className = "ml-1 opacity-60 hover:opacity-100";
                removeButton.setAttribute("aria-label", `Remove ${skill}`);
                removeButton.textContent = "×";

                removeButton.addEventListener("click", function () {
                    skills.splice(index, 1);
                    syncHidden();
                    render();
                });

                chip.appendChild(icon);
                chip.appendChild(text);
                chip.appendChild(removeButton);

                box.insertBefore(chip, input);
            });

            syncHidden();
        }

        function addSkill(value) {
            const skill = value.trim();

            if (!skill) return;

            const exists = skills.some(
                existing =>
                    existing.toLowerCase() === skill.toLowerCase()
            );

            if (!exists) {
                skills.push(skill);
            }

            input.value = "";
            render();
        }

        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === ",") {
                event.preventDefault();
                addSkill(input.value);
            }

            if (
                event.key === "Backspace" &&
                input.value === "" &&
                skills.length > 0
            ) {
                skills.pop();
                render();
            }
        });

        box.addEventListener("click", function () {
            input.focus();
        });

        loadInitialSkills();
        render();
    }


    setupSkillBox(
        "req-box",
        "req-input",
        "req-hidden",
        "required"
    );

    setupSkillBox(
        "pref-box",
        "pref-input",
        "pref-hidden",
        "preferred"
    );
});