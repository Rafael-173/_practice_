document.addEventListener("DOMContentLoaded", function () {

    //БУРГЕР-МЕНЮ
    const toggle = document.querySelector(".menu-toggle");
    const menu = document.querySelector("#main-navigation");

    if (toggle && menu) {
        function closeMenu() {
            menu.classList.remove("is-open");
            toggle.setAttribute("aria-expanded", "false");
            toggle.setAttribute("aria-label", "Открыть меню");
        }

        toggle.addEventListener("click", function () {
            const isOpen = toggle.getAttribute("aria-expanded") === "true";
            if (isOpen) {
                closeMenu();
            } else {
                menu.classList.add("is-open");
                toggle.setAttribute("aria-expanded", "true");
                toggle.setAttribute("aria-label", "Закрыть меню");
            }
        });

        menu.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeMenu);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") closeMenu();
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth > 768) closeMenu();
        });
    }

   //фильтрация
    const form = document.getElementById("filters-form");
    const container = document.getElementById("groups-container");

    if (form && container) {
        async function loadGroups() {
            const params = new URLSearchParams(new FormData(form)).toString();
            const url = window.location.pathname + (params ? "?" + params : "");

            container.innerHTML = "<p>Загрузка...</p>";

            try {
                const response = await fetch(url, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                });

                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }

                const data = await response.json();
                container.innerHTML = data.html;
            } catch (err) {
                container.innerHTML = "<p>Не удалось загрузить данные. Попробуйте ещё раз.</p>";
                console.error("Ошибка фильтрации:", err);
            }
        }

        // Фильтрация сразу при смене select — кнопка не нужна
        form.addEventListener("change", function (e) {
            e.preventDefault();
            loadGroups();
        });

        // Страховка от перезагрузки при Enter
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            loadGroups();
        });
    }

});