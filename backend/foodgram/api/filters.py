from django_filters import rest_framework as filters
from rest_framework.exceptions import AuthenticationFailed

from recipes.models import Recipes, Tag


class CustomFilters(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    author = filters.NumberFilter(field_name='author')

    is_favorited = filters.BooleanFilter(field_name='is_favorited',
                                         method='get_is_favorited',
                                         exclude=True, lookup_expr=True)

    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='get_is_in_shopping_cart'
    )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            raise AuthenticationFailed(
                'Вы не авторизованы. Авторизуйтесь'
            )
        if name == 'is_favorited' and value:
            return queryset.filter(recipes_favorite_recipes__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            raise AuthenticationFailed(
                'Вы неавторизованы. Авторизуйтесь'
            )
        if name == 'is_in_shopping_cart' and value:
            return queryset.filter(recipes_shopping_cart_recipes__user=user)
        return queryset

    class Meta:
        model = Recipes
        fields = ['tags', 'author', "is_in_shopping_cart", "is_favorited"]
