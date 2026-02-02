document.addEventListener("DOMContentLoaded", function () {
    const modal = document.querySelector("section");
    const openButtons = document.querySelectorAll(".card-button");
    const closeButton = document.querySelector(".close-btn");
    const overlay = document.querySelector(".overlay");
    
    openButtons.forEach(button => {
        button.addEventListener("click", function () {
            modal.classList.add("active");
        });
    });
    
    closeButton.addEventListener("click", function () {
        modal.classList.remove("active");
    });
    
    overlay.addEventListener("click", function () {
        modal.classList.remove("active");
    });
});
