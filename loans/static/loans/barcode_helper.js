// Disallow rapidly typing enter after last digit, for better support
// for barcode scanners

function isLoading(el) {
  return el.querySelector(".loading-results");
}

function avoidRapidEnter(event) {
  const element = event.target;
  const parent = element.parentNode.parentNode;

  if (
    (event.key === "Enter" || event.keyCode === 13)
    && isLoading(parent)
  ) {
    event.stopImmediatePropagation();
  }
}

let listenerAttached = {};

function barcodeHelper() {
  const body = document.body;

  const bodyObserver = new MutationObserver((mutations) => {
    for (const mutation of mutations.filter((m) => m.type === "childList")) {
      const search = body.querySelector(".select2-search__field");
      const results = body.querySelector(".select2-results");

      if (search) {
        const id = search.getAttribute("aria-controls");

        if (!listenerAttached[id]) {
          search.addEventListener("keydown", avoidRapidEnter, true);
          listenerAttached[id] = true;
        }

        break;
      }
    }
  })

  bodyObserver.observe(body, {childList: true, subtree: true})
}


document.addEventListener("DOMContentLoaded", barcodeHelper);
