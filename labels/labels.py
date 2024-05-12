from dataclasses import dataclass, fields

from django.utils.translation import gettext as _
from fpdf import FPDF
from fpdf.fpdf import PAGE_FORMATS
from isbnlib import mask
from PIL import ImageColor

from .barcodes import get_barcode_image


@dataclass
class PageConfiguration:
    paper_size: str
    n_rows: int
    n_cols: int
    margin_top: int
    margin_right: float
    margin_bottom: float
    margin_left: float
    horizontal_gap: float
    vertical_gap: float
    font_size: float
    use_color: bool
    use_border: bool
    include_barcode: bool
    use_isbn: bool

    box_w: float = None
    box_h: float = None
    paper_width: float = None
    paper_height: float = None

    def __post_init__(self):
        if "," in self.paper_size:
            self.paper_width, self.paper_height = map(
                float, self.paper_size.split(",", 1)
            )
            self.paper_size = (self.paper_width, self.paper_height)
        else:
            self.paper_width, self.paper_height = PAGE_FORMATS[
                self.paper_size.lower()
            ]

            # unit conversion factor from fpdf's default to mm
            k = 0.3527751646284102
            self.paper_width *= k
            self.paper_height *= k

        self.box_h = (
            self.paper_height
            - self.margin_top
            - self.margin_bottom
            - self.vertical_gap * (self.n_rows - 1)
        ) / self.n_rows
        self.box_w = (
            self.paper_width
            - self.margin_left
            - self.margin_right
            - self.horizontal_gap * (self.n_cols - 1)
        ) / self.n_cols


def get_color(color):
    return ImageColor.getcolor(color, "RGB")


class LabelPDF(FPDF):
    n_labels = 0

    def __init__(self, obj, conf):
        enum_fields = {f.name for f in fields(PageConfiguration)}
        obj_fields = {f.name for f in obj._meta.get_fields()}
        conf_fields = {f.name for f in conf._meta.get_fields()}

        kwargs = {f: getattr(conf, f) for f in conf_fields & enum_fields}
        kwargs |= {f: getattr(obj, f) for f in obj_fields & enum_fields}

        self.conf = PageConfiguration(**kwargs)

        super().__init__("portrait", "mm", self.conf.paper_size)

        self.set_font("Helvetica", "", self.conf.font_size)
        self.set_margins(
            self.conf.margin_left,
            self.conf.margin_top,
            self.conf.margin_right,
        )
        self.set_auto_page_break(0)
        self.n_labels = 0

    def walk(self, x, y):
        self.set_xy(self.get_x() + x, self.get_y() + y)

    def new_page(self):
        self.add_page()
        self.set_xy(self.conf.margin_left, self.conf.margin_top)

    def label(self):
        """Creates label box and returns original position"""
        x, y = self.get_x(), self.get_y()

        self.n_labels += 1

        is_new_row = False
        if (self.n_labels % self.conf.n_cols) == 0:
            is_new_row = True

        if (self.n_labels % (self.conf.n_cols * self.conf.n_rows)) == 1:
            self.new_page()
            x, y = self.get_x(), self.get_y()

        self.cell(
            self.conf.box_w,
            self.conf.box_h,
            border=1 if self.conf.use_border else 0,
        )

        if is_new_row:
            self.ln(h=self.conf.vertical_gap)
        else:
            self.walk(self.conf.horizontal_gap, 0)

        return x, y

    def entry(self, specimen):
        color = specimen.book.classification.location.color
        barcode = specimen.book.canonical_isbn and self.conf.include_barcode
        barcode_prop = 2 / 3

        if color and self.conf.use_color:
            self.set_draw_color(*get_color(color))

        label_x, label_y = self.label()
        next_x, next_y = self.get_x(), self.get_y()
        self.set_xy(label_x, label_y)

        words = [
            specimen.book.code,
            specimen.book.classification.abbreviation,
            specimen.book.classification.location.name,
            # Translators: abbreviation of specimen
            _("Ex. %(n)s") % {"n": specimen.number},
        ]

        for word in words:
            self.cell(
                w=self.conf.box_w * (1 - barcode_prop if barcode else 1),
                h=self.conf.box_h / len(words),
                new_x="left",
                new_y="next",
                text=word,
                border="B" if self.conf.use_color else 0,
            )

        if barcode:
            self.set_xy(
                label_x + self.conf.box_w * (1 - barcode_prop) + 0.5,
                label_y + 0.5,
            )
            width = self.conf.box_w * barcode_prop - 1
            height = self.conf.box_h * (4 / 5) - 1
            number = (
                specimen.book.canonical_isbn
                if self.conf.use_isbn
                else specimen.id
            )
            self.image(
                get_barcode_image(
                    number=number,
                    width=width,
                    height=height,
                ),
                keep_aspect_ratio=True,
                w=width,
                h=height,
            )
            self.set_font("Helvetica", "", self.conf.font_size * 0.85)
            self.cell(
                text=mask(number) if self.conf.use_isbn else str(number),
                align="C",
                w=width,
                h=self.conf.box_h - height - 2,
            )
            self.set_font("Helvetica", "", self.conf.font_size)

        self.set_xy(next_x, next_y)


def create(obj):
    pdf = LabelPDF(obj, obj.configuration)

    for specimen in obj.specimens.all():
        pdf.entry(specimen)

    return pdf.output()


def create_file(obj, filename):
    content = create(obj)

    if content:
        with open(filename, "wb") as f:
            f.write(content)
