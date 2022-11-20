from http import HTTPStatus
from django.test import Client, TestCase


class AboutURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_correct_urls(self) -> None:
        """Страница доступка по URL."""
        pages: tuple = ('/about/author/', '/about/tech/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self) -> None:
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names: dict = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
