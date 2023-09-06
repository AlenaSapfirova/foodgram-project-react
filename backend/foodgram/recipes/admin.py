from django.contrib import admin

from .models import (
    Amount,
    Tag,
    Recipes,
    Ingredient,
    Favorite,
    Shopping_Cart
)
from users.models import Subscription


class AmountInline(admin.TabularInline):
    model = Amount


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['recipes', 'user']
    list_display_links = None
    list_editable = ['recipes', 'user']


class Shopping_CartAdmin(admin.ModelAdmin):
    list_display = ['recipes', 'user']
    list_display_links = None
    list_editable = ['recipes', 'user']


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'author']
    list_display_links = None
    list_editable = ['user', 'author']


class IngredientAdmin(admin.ModelAdmin):
    inlines = [AmountInline]
    list_display = ['name', 'measurement_unit']
    list_filter = ['name', 'measurement_unit']


class RecipesAdmin(admin.ModelAdmin):
    inlines = [AmountInline]
    list_display = ['name', 'text', 'cooking_time', 'image',
                    'author', 'id']
    filter_horizontal = ('tags',)


class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'slug']
    list_display_links = None
    list_editable = ['name', 'color', 'slug']


admin.site.register(Shopping_Cart, Shopping_CartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(Amount)
admin.site.register(Ingredient, IngredientAdmin)
# admin.site.register(RecipeTag)
admin.site.register(Subscription, SubscriptionAdmin)
# admin.site.register(User, UserAdmin)
