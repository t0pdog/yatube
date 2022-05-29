from itertools import islice

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')
        # Создаем подписчика
        cls.follower_user = User.objects.create_user(username='follower_user')
        # Создаем неподписчика
        cls.not_follower = User.objects.create_user(username='not_follower')

        cls.group = Group.objects.create(
            title='test-group',
            slug='group-slug',
            description='group-description'
        )
        cls.group2 = Group.objects.create(
            title='test-group2',
            slug='group-slug2',
            description='group-description2'
        )

        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group
        )

        cls.comment = Comment.objects.create(
            text='Тестовый comment',
            author=cls.user,
            post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.follower_user)
        
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.not_follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'group-slug'}):
            'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': '1'}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': '1'}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста страниц

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response.context.get('posts')[0],
            PostPagesTests.post
        )
        self.assertEqual(
            response.context.get('title'),
            'Последние обновления на сайте'
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group-slug'})
        )
        self.assertEqual(
            response.context.get('posts')[0],
            PostPagesTests.post
        )
        self.assertEqual(
            response.context.get('title'),
            'Записи сообщества test-group'
        )
        self.assertEqual(
            response.context.get('group').title,
            PostPagesTests.group.title
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(
            response.context.get('posts')[0], PostPagesTests.post
        )
        self.assertEqual(
            response.context.get('title'),
            'Профайл пользователя HasNoName'
        )
        self.assertEqual(response.context.get('posts_count'), 1)
        self.assertEqual(
            response.context.get('username'), 'HasNoName'
        )
        self.assertEqual(
            response.context.get('author'), PostPagesTests.user
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(
            response.context.get('post'), PostPagesTests.post
        )
        self.assertEqual(
            response.context.get('title'), 'Пост Тестовый заголо'
        )
        self.assertEqual(
            response.context.get('posts_count'), 1
        )
        self.assertEqual(
            response.context.get('author'), PostPagesTests.user
        )
        self.assertEqual(
            response.context.get('comments')[0].text, 'Тестовый comment'
        )

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_create'
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form'
                ).fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': '1'}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form'
                ).fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_group_shown_if_group_added(self):
        """
        Если при создании поста указать группу,
        убедимся что пост не попал в другую группу.
        """
        response = self.authorized_client.get(reverse(
            'posts:index'
        ))
        self.assertNotEqual(
            response.context.get('posts')[0].group.title, 'test-group2'
        )

    def test_index_cache(self):
        """Тесты, которые проверяют работу кеша index."""
        # Запрос главной страницы до добавления поста
        response1 = self.guest_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Тест заголовок2',
            author=self.user,
        )
        # Запрос главной страницы после добавления поста
        response2 = self.guest_client.get(reverse('posts:index'))
        # Проверка кеша
        self.assertEqual(response1.content, response2.content)
        # Сбросили кеш
        cache.clear()
        # Проверяем что теперь новый пост появился на странице
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response1.content, response3.content)

    def test_user_follows(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""

        # Подписываемся
        self.authorized_client2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author.username}
        ))
        response = self.authorized_client2.get(reverse(
            'posts:follow_index',
        ))
        self.assertEqual(len(response.context['page_obj']), 1)
        # Отписываемся
        self.authorized_client2.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post.author.username}
        ))
        response = self.authorized_client2.get(reverse(
            'posts:follow_index',
        ))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_user_follows(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""

        # Подписывается follower_user
        self.authorized_client2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author.username}
        ))
        # Создаем ещё 1 пост
        Post.objects.create(
            text='Тест заголовок2',
            author=self.user,
        )
        # Проверяем что в ленте подписчика появился ещё пост
        response = self.authorized_client2.get(reverse(
            'posts:follow_index',
        ))
        self.assertEqual(len(response.context['page_obj']), 2)
        # Проверяем что в ленте неподписчика нет постов
        response = self.authorized_client3.get(reverse(
            'posts:follow_index',
        ))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')

        cls.group = Group.objects.create(
            title='test-group',
            slug='group-slug',
            description='group-description'
        )
        cls_post = Post(
            text='Тестовый заголовок',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group
        )
        batch_size = 13
        objs = (cls_post for i in range(13))
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
