from django_filters import rest_framework as filters

from recipes.models import Tag, Recipes


class CustomFilters(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all())
    author = filters.NumberFilter(field_name='author')
    is_favorited = filters.BooleanFilter(field_name='is_favorited',
                                         method='filter_params_favorite')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_params_shopping'
    )

    def filter_params_favorite(self, name, queryset, value):
        if self.request.user.is_anonymous:
            return queryset
        return queryset.filter(favorite__user=self.request.user)

    def filter_params_shopping(self, name, queryset, value):
        if self.request.user.is_anonymous:
            return queryset
        return queryset.filter(shopping_cart__user=self.request.user)

    class Meta:
        model = Recipes
        fields = ['tags', 'author']
