// Inspired by the great answer by Mikael Dúi Bolinder
// at https://stackoverflow.com/a/78089783

function hideOnClickOutside(element, hideCallback) {
  const outsideClickListener = event => {
    if (
      !element.contains(event.target)
      && !buttonElement.contains(event.target)
    ) {
      hideCallback(element);
      removeClickListener();
    }
  }

  const removeClickListener = () => {
    document.removeEventListener('click', outsideClickListener);
  }

  document.addEventListener('click', outsideClickListener);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      hideCallback(element);
    }
  });
}


let barcodeDetector, targetElement, searchButton, videoElement, buttonElement;

window.addEventListener('load', function () {
  searchButton = document.querySelector("#searchbar + input");
  targetElement = document.querySelector("#searchbar");
  videoElement = document.querySelector("video.barcode-video");
  buttonElement = document.querySelector(".barcode-button");

  try { window['BarcodeDetector'].getSupportedFormats() }
  catch { window['BarcodeDetector'] = barcodeDetectorPolyfill.BarcodeDetectorPolyfill }

  // Create a BarcodeDetector for simple retail operations.
  barcodeDetector = new BarcodeDetector({
    formats: ["ean_13", "ean_8", "upc_a", "upc_e"]
  });

})

async function readBarcode() {
  if (!window['BarcodeDetector']) {
    console.log("Barcode detection not available in this browser. Quitting...")
  }

  showVideo();
  hideOnClickOutside(videoElement.parentNode, hideVideo)

  // Get a stream for the rear camera, else the front (or side?) camera.
  videoElement.srcObject = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: 'environment' }
  });

  while (videoIsShown()) {
    // Try to detect barcodes in the current video frame.
    const barcodes = await barcodeDetector.detect(videoElement);

    // Continue loop if no barcode was found.
    if (barcodes.length == 0)
    {
      // Scan interval 50 ms like in other barcode scanner demos.
      // The higher the interval the longer the battery lasts.
      await new Promise(r => setTimeout(r, 100));
      continue;
    }


    // Notify user that a barcode has been found.
    try {
      navigator.vibrate(200);
    } catch {}

    // We expect a single barcode.
    // It's possible to compare X/Y coordinates to get the center-most one.
    // One can also do "preferred symbology" logic here.
    const value = choosePreferred(barcodes)
    yieldValue(value)
    hideVideo();
    searchButton.click();
    break;
  }
}

function choosePreferred(barcodes) {
  let chosen = barcodes[0];
  if (barcodes.length > 1) {
    const goodFormat = barcodes.filter(x => x.format === "ean_13");
    if (goodFormat.length > 0) {
      chosen = goodFormat[0];
    }
  }

  return chosen.rawValue;
}

function yieldValue(value) {
  targetElement.value = value
}

function hideVideo() {
  videoElement.parentNode.style.setProperty("display", "none");
}

function showVideo() {
  videoElement.parentNode.style.setProperty("display", "flex");
}

function videoIsShown() {
  return videoElement && videoElement.parentNode.style.getPropertyValue("display") == "flex";
}

