from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для создания поста."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}


class CommentForm(forms.ModelForm):
    """Форма для создания комментариев."""
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}
