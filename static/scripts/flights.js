document.addEventListener("DOMContentLoaded", () => {
    const $modalCloseButtons = document.querySelectorAll("button.modal-close");
    $modalCloseButtons.forEach(closeButton => {
        const modal = closeButton.parentElement;
        closeButton.addEventListener("click", () => {
            modal.classList.remove("is-active");
        });
    });

    const $flightDetailButtons = document.querySelectorAll("span.flight-duration.clickable");
    $flightDetailButtons.forEach(details => {
        const modal = details.parentElement.parentElement.querySelector("article.modal");
        details.addEventListener("click", () => {
            modal.classList.add("is-active");
        })
    });

    const $fareDetailButtons = document.querySelectorAll(".flight-fare.clickable");
    $fareDetailButtons.forEach(details => {
        const modal = details.parentElement.querySelector("article.modal");
        details.addEventListener("click", () => {
            modal.classList.add("is-active");
        })
    });
});