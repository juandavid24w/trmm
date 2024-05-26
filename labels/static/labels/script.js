document.addEventListener("DOMContentLoaded", () => {
  const value = JSON.parse(document.getElementById('save-button-label').textContent);
  const save = document.querySelector('[name="_continue"]');
  save.value = value;
})
