from django.forms.widgets import TextInput


class BarcodeTextInput(TextInput):
    template_name = "barcodes/text.html"

    class Media:
        css = {"all": ["barcodes/style.css"]}
        js = [
            "barcodes/script.js",
            "https://cdn.jsdelivr.net/npm/@undecaf/zbar-wasm@0.9.15/dist/index.js",
            "https://cdn.jsdelivr.net/npm/@undecaf/barcode-detector-polyfill"
            + "@0.9.20/dist/index.js",
        ]
