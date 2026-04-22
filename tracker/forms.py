from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['url', 'desired_price']
        widgets = {
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Вставьте ссылку на товар'}),
            'desired_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Желаемая цена'}),
        }
        labels = {
            'url': 'Ссылка на товар',
            'desired_price': 'Желаемая цена (₽)',
        }