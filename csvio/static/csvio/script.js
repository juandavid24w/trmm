let select;

function populateFields() {
  const mandatoryEl = document.getElementById("mandatory-fields");
  const optionalEl = document.getElementById("optional-fields");

  const data = JSON.parse(document.getElementById('csvio-data').textContent);
  const {mandatory, optional} = data[select.value];

  mandatoryEl.innerHTML = mandatory.join(", ");
  optionalEl.innerHTML = optional.join(", ");
}

document.addEventListener("DOMContentLoaded", () => {
  select = document.getElementById("id_key");

  populateFields()
  select.addEventListener("change", populateFields);
})
