from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


#  создали собственный класс для формы регистрации
class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # модель, с которой связана создаваемая форма:
        model = User

        fields = ('first_name', 'last_name', 'username', 'email')
