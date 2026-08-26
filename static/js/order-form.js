const addButton = document.querySelector("[data-add-item]");
const formset = document.querySelector(".item-formset");
const template = document.querySelector("#empty-item-form");

if (addButton && formset && template) {
  addButton.addEventListener("click", () => {
    const prefix = formset.dataset.formsetPrefix;
    const totalForms = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
    const index = Number(totalForms.value);
    const html = template.innerHTML.replaceAll("__prefix__", index);

    formset.insertAdjacentHTML("beforeend", html);
    totalForms.value = index + 1;
  });
}
