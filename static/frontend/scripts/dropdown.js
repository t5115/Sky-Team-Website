/*Script responsible for the drop down menu */

const toggle = document.getElementById("dropdownToggle");
const menu = document.getElementById("dropdownMenu");

toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.classList.toggle("show");
});

document.addEventListener("click", () => {
    menu.classList.remove("show");
});
