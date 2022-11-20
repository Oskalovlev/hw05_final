from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
# from django.views.decorators.cache import cache_page

from .models import Group, Post, Comment, Follow, User
from .forms import PostForm, CommentForm


def paginations(page_number, page_list):
    paginator = Paginator(page_list, settings.NUMBER_OF_POSTS)
    return paginator.get_page(page_number.GET.get('page'))


# @cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group')
    page_obj = paginations(page_number=request, page_list=post_list)
    context = {
        'page_obj': page_obj,
        'show_group_link': True,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.select_related('author')
    page_obj = paginations(page_number=request, page_list=group_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.select_related('group')
    page_obj = paginations(page_number=request, page_list=author_posts)
    following = (Follow.objects.filter(
        user=request.user, author=author
    ).exists() and request.user if request.user.is_authenticated else False)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id
    )
    form = CommentForm(request.POST)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


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
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).all()
    page_obj = paginations(page_number=request, page_list=post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
