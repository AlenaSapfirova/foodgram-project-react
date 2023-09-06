from django_filters import rest_framework as filters

from recipes.models import Tag, Recipes
from users.models import User


class CustomFilters(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(fields_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    author = filters.ModelChoiceFilter(User.objects.all())
    is_favorited = filters.BooleanFilter(field_name='is_favorited',
                                         method='filter_params')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_params'
    )

    def filter_params(self, name, queryset, value):
        if self.request.user.is_anonymous:
            return queryset
        if name == 'is_favorited' and value:
            return queryset.filter(favorite__user=self.request.user)
        if name == 'is_in_shopping_cart' and value:
            return queryset.filter(shopping_cart__user=self.request.user)

    class Meta:
        model = Recipes
        fields = ['tags', 'author']

