const item_template       = document.getElementById("dropdown_element_template").content;
const divider_template    = document.getElementById("dropdown_divider"         ).content;
const progress_item       = document.getElementById("dropdown_progress_item"   ).content;
const error_item_template = document.getElementById("error_item_template"      ).content;

const oneWaySwitch  = document.getElementById("one_way"                    );
const returnOnField = document.querySelector ("input.input[name=return_on]");

const mainForm = document.forms[0];
const hiddenFields = mainForm.querySelectorAll("input[hidden]");

function fillField(field, location) {
    return function() {
        const target = document.getElementById(field.dataset.target);
        target.value = location.iataCode;
        field.value = `${location.iataCode}, ${location.name} Airport - ${location.address.cityName}`;
        field.parentElement.parentElement.classList.remove("is-active");
        field.setCustomValidity(""); field.reportValidity();
    }
}
/**
 * @param {Element} field
 */
function addListenersToLocationField(field) {
    const dropdown         = field.parentElement.parentElement;
    const dropdown_content = dropdown.querySelector(".dropdown-menu .dropdown-content");
    field.addEventListener("focus" , () => {
        if(dropdown_content.querySelectorAll(".tag").length > 0)
            dropdown.classList.add("is-active");
    });
    field.addEventListener("blur" , () => {
        dropdown.classList.remove("is-active");
    });
    field.addEventListener("input", () => {
        if(field.value.length > 0) {
            field.setCustomValidity(""); field.reportValidity();
            dropdown_content.textContent = "";
            dropdown_content.append(progress_item.cloneNode(true));
            dropdown.classList.add("is-active");
            fetch(`/iatacodes?query=${field.value}`)
            .then(response => {
                if(!response.ok) throw new Error(response.statusText);
                return response.json();
            })
            .then(data => {
                if((data.length ?? 0) == 0) throw new Error("No airports found.");
                dropdown_content.textContent = "";
                data.forEach((location, i) => {
                    if(i > 0) dropdown_content.append(divider_template.cloneNode(true));
                    dropdown_content.append(document.importNode(item_template, true));
                    const item = dropdown_content.lastElementChild;
                    item.querySelector("p[name=city]"      ).textContent = `${location.address.cityName}, ${location.address.countryName}`;
                    item.querySelector("span[name=code]"   ).textContent = location.iataCode;
                    item.querySelector("span[name=airport]").textContent = location.name + " Airport";
                    item.addEventListener("mousedown", fillField(field, location));
                });
            })
            .catch(_ => {
                dropdown_content.textContent = "";
                const error_item = error_item_template.cloneNode(true);
                error_item.getElementById("message").textContent = "No matching airports found. Try again with different keywords."
                dropdown_content.append(error_item);
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const $navbarBurgers = document.querySelectorAll('.navbar-burger');
    if ($navbarBurgers.length > 0) {
        $navbarBurgers.forEach( el => {
            el.addEventListener('click', () => {
                const target = el.dataset.target;
                const $target = document.getElementById(target);
                el.classList.toggle('is-active');
                $target.classList.toggle('is-active');
            });
        });
    }

    const $locationFields = document.querySelectorAll("input.input[type=text]");
    $locationFields.forEach(addListenersToLocationField);

    returnOnField.disabled = oneWaySwitch.checked;
    returnOnField.required = !oneWaySwitch.checked;
    oneWaySwitch.addEventListener("change", () => {
        returnOnField.disabled = !returnOnField.disabled;
        returnOnField.required = !returnOnField.disabled;
    });

    mainForm.addEventListener("submit", e => {
        for(let field of hiddenFields) {
            if(field.value.length === 0) {
                const target = document.querySelector(`input[name=${field.id}]`);
                target.setCustomValidity("Please select a location from the dropdown menu.");
                target.reportValidity();
                e.preventDefault(); return false;
            }
        }
        return true;
    });
});