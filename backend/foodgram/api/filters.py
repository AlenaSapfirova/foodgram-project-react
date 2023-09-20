from django_filters import rest_framework as filters

from recipes.models import Tag, Recipes


class CustomFilters(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    author = filters.NumberFilter(field_name='author')
    is_favorited = filters.BooleanFilter(field_name='is_favorited',
                                         method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='get_is_in_shopping_cart'
    )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value and name:
            return queryset.filter(recipes_favorite_recipes__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value and name == 'is_favorited':
            return queryset.filter(recipes_shopping_cart_recipes__user=user)
        return queryset

    class Meta:
        model = Recipes
        fields = ['tags', 'author', "is_in_shopping_cart", "is_favorited"]

    # def get_is_favorited(self, name, queryset, value):
    #     user = self.request.user
    #     if user.is_authenticated and value:
    #         return queryset.filter(recipes_favorite_recipes__user=user)
    #     return queryset

    # def get_is_in_shopping_cart(self, name, queryset, value):
    #     user = self.request.user
    #     if user.is_authenticated and value:
    #         return queryset.filter(recipes_shopping_cart_recipes__user=user)
    #     return queryset
