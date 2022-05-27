from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, Follow
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required


def paginator_func(queryset, request):

    paginator = Paginator(queryset, 10)
    # Из URL извлекаем номер запрошенной страницы - значение page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    title = 'Последние обновления на сайте'
    posts = Post.objects.all()
    # В словаре context отправляем информацию в шаблон
    context = {
        'posts': posts,
        'title': title,
    }
    context.update(paginator_func(posts, request))
    return render(request, 'posts/index.html', context)


# Страница с постами группы
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    title = f'Записи сообщества {group}'
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
        'title': title,
    }
    context.update(paginator_func(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):

    author = get_object_or_404(User, username=username)
    title = f'Профайл пользователя {author}'
    posts = Post.objects.filter(author=author)
    template = 'posts/profile.html'
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'username': username,
        'posts': posts,
        'title': title,
        'posts_count': author.posts.count(),
        'following': following,
    }
    context.update(paginator_func(posts, request))
    
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    title = f'Пост {post}'

    form = CommentForm()

    # комментарии достаем через релейтед нейм "comments"
    comments = post.comments.all()

    context = {
        'post': post,
        'author': author,
        'title': title,
        'posts_count': author.posts.count(),
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    title = 'Добавить запись'
    button = 'Добавить'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post_create = form.save(commit=False)
        post_create.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)

    context = {
        'form': form,
        'title': title,
        'button': button,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    title = 'Редактировать запись'
    button = 'Сохранить'
    post = get_object_or_404(Post, id=post_id)

    is_edit = True
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    else:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit,
        'title': title,
        'button': button,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):

    post = get_object_or_404(Post, id=post_id)

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Посты авторов, на которых вы подписаны'
    user = request.user
    posts = Post.objects.filter(author__following__user=user)

    context = {
        'posts': posts,
        'title': title,
    }
    context.update(paginator_func(posts, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    user=request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.create(
            author=author,
            user=request.user,
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    author = get_object_or_404(User, username=username)

    Follow.objects.get(
        author=author,
        user=request.user,
    ).delete()
    return redirect('posts:follow_index')
