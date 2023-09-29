from django_filters import rest_framework as filters
# from distutils.util import strtobool
# from rest_framework.response import Response
# from rest_framework import status

from recipes.models import Recipes, Tag

CHOICES_LIST = (
    ('0', 'False'),
    ('1', 'True')
)


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
        queryset = Recipes.objects.all()
        user = self.request.user
        if user.is_authenticated and name == 'is_favorited':
            return queryset.filter(recipes_favorite_recipes__user=user)
        return queryset.none()
        # return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and name == 'is_in_shopping_cart':
            return queryset.filter(recipes_shopping_cart_recipes__user=user)
        return []
        # return Response(status=status.HTTP_401_UNAUTHORIZED)

    class Meta:
        model = Recipes
        fields = ['tags', 'author', "is_in_shopping_cart", "is_favorited"]
