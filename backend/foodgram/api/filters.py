from django_filters import rest_framework as filters
from distutils.util import strtobool
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipes, Tag, Favorite


CHOICES_LIST = (
    ('0', 'False'),
    ('1', 'True')
)


class CustomFilters(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    author = filters.NumberFilter(field_name='author')

    # is_favorited = filters.BooleanFilter(field_name='is_favorited',
    #                                      method='get_is_favorited')
    is_favorited = filters.AllValuesMultipleFilter(
        choices=CHOICES_LIST,
        method='is_favorited_method'
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        choices=CHOICES_LIST,
        method='is_in_shopping_cart_method'
    )
    # is_in_shopping_cart = filters.BooleanFilter(
    #     field_name='is_in_shopping_cart',
    #     method='get_is_in_shopping_cart'
    # )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.none()
        favorites = Favorite.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in favorites]
        new_queryset = queryset.filter(id__in=recipes)

        if not strtobool(value):
            return queryset.difference(new_queryset)

        return queryset.filter(id__in=recipes)
        # if (user.is_authenticated and value is True
        #    and name == 'is_favorited'):
        # return queryset.filter(recipes_favorite_recipes__user=user)
        # if not value and user.is_anonymous:
        #     return self.queryset.none()
        # return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if (
            user.is_authenticated and value is True
            and name == 'is_in_shopping_cart'
        ):
            return queryset.filter(recipes_shopping_cart_recipes__user=user)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    class Meta:
        model = Recipes
        fields = ['tags', 'author', "is_in_shopping_cart", "is_favorited"]
