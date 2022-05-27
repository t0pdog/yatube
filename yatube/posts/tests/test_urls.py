from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')

        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.user
        )
        Group.objects.create(
            title='test-group',
            slug='group-slug',
            description='group-description'
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/group-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_templates_url_unauth(self):
        """Тесты доступности страниц для
        неавторизованного пользователя"""
        templates_url_unauth = [
            '/',
            '/group/group-slug/',
            '/posts/1/',
            '/profile/HasNoName/'
        ]
        for address in templates_url_unauth:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        response = self.guest_client.get('/posts/2/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Для авторизованного пользователя
    def test_create_post_auth(self):
        """Тесты доступности страниц для
        авторизованного пользователя"""
        templates_url_unauth = [
            '/create/',
            '/posts/1/edit/'
        ]
        for address in templates_url_unauth:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_unauth(self):
        """Редирект неавторизованного пользователя
        при создании поста."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_edit_post_unauth(self):
        """Редирект неавторизованного пользователя
        при редактировании поста."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_create_comment_auth(self):
        """Редирект авторизованного пользователя
        при создании комментария."""
        response = self.authorized_client.get(
            '/posts/1/comment/', follow=True
        )
        self.assertRedirects(response, '/posts/1/')

    def test_create_comment_auth(self):
        """Редирект неавторизованного пользователя
        при создании комментария."""
        response = self.guest_client.get(
            '/posts/1/comment/', follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/comment/'
        )
