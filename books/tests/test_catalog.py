from django.test import TestCase

from ..models import Book, Classification, Location, Specimen


def create_test_catalog():
    l1 = Location.objects.create(name="Loc1", color="#000000")
    l2 = Location.objects.create(name="Loc2", color="#ffffff")

    c1 = Classification.objects.create(
        abbreviation="c1",
        name="Class1",
        location=l1,
    )
    c2 = Classification.objects.create(
        abbreviation="c2",
        name="Class2",
        location=l1,
    )
    c3 = Classification.objects.create(
        abbreviation="c3",
        name="Class3",
        location=l2,
    )
    c4 = Classification.objects.create(
        abbreviation="c4",
        name="Class4",
        location=l2,
    )

    book = Book.objects.create(
        isbn=None,
        title="Histórias apócrifas",
        author_first_names="Karen",
        author_last_name="Tchápek",
        publisher="Editora",
        classification=c1,
    )
    for _ in range(4):
        book.specimens.create()

    Book.objects.create(
        isbn="8500912596",
        title="Amor de perdicao",
        author_first_names="Camilo Castelo",
        author_last_name="Branco",
        publisher="Tecnoprint",
        classification=c1,
    )

    book = Book.objects.create(
        isbn="8535907661",
        title="Operação cetro dourado",
        author_first_names="Julian",
        author_last_name="Press",
        publisher="Companhia Das Letras",
        classification=c2,
    )
    for _ in range(2):
        book.specimens.create()

    book = Book.objects.create(
        isbn="None",
        title="A vida quotidiana dos Astecas na véspera da conquista espanhola",
        author_first_names="Jacques",
        author_last_name="Soustelle",
        publisher="Editora Itatiaia",
        classification=c3,
    )
    for _ in range(8):
        book.specimens.create()

    book = Book.objects.create(
        isbn="9788577992706",
        title="O estrangeiro",
        author_first_names="Albert",
        author_last_name="Camus",
        publisher="Edições Bestbolso",
        classification=c4,
    )
    for _ in range(3):
        book.specimens.create()


class CatalogTestCase(TestCase):
    def setUp(self):
        create_test_catalog()

    def test_catalog(self):
        self.assertTrue(Book.objects.all())
        self.assertTrue(Specimen.objects.all())
        self.assertTrue(Location.objects.all())
        self.assertTrue(Classification.objects.all())
