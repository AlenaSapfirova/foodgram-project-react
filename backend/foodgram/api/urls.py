from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
)

# handler404 = 'api.views.handler404'


router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('recipes',
                RecipesViewSet,
                basename='recipes')
router.register('ingredients', IngredientViewSet)
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),

    path('auth/', include('djoser.urls.authtoken')),
]
