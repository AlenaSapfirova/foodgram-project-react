from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import exceptions, status, viewsets
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .pagination import CustomPaginator
from recipes.models import (
    Tag,
    Recipes,
    Ingredient,
    Shopping_Cart,
    Favorite
)
from .serializers import (
    CustomUserSerializer,
    TagSerializer,
    IngredientSerializer,
    SubscriptionSerializer,
    GetRecipesSerializer,
    CreateUpdateRecipesSerializer,
    ShortViewRecipesSerializers
)
from .permissions import AuthorOrReadOnly

from users.models import User, Subscription
from .filters import CustomFilters


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action(detail=False, permission_classes=[IsAuthenticated, ],
            serializer_class=SubscriptionSerializer, methods=['get'])
    def subscriptions(self, request):
        query = User.objects.get(id=request.user.id)
        queryset = query.user.all()
        serializer = SubscriptionSerializer(queryset, many=True,
                                            context={'request': request})
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(serializer_class=SubscriptionSerializer,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ], detail=True)
    def subscribe(self, request, id):
        if request.method == "POST":
            user = request.user
            author = get_object_or_404(User, id=id)
            if Subscription.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError('подписка уже оформлена')
            else:
                Subscription.objects.create(user=user, author=author)
                serializer = self.get_serializer(author)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            author = get_object_or_404(User, id=id)
            user = request.user
            subscribe = Subscription.objects.filter(user=user, author=author)
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name', )


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPaginator
    filterset_class = CustomFilters
    permission_classes = (AuthorOrReadOnly,)

    def perform_create(self, serializer):
        author = self.request.user
        serializer.save(author=author)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GetRecipesSerializer
        return CreateUpdateRecipesSerializer

    @action(detail=True, methods=['post', 'delete'],
            serializer_class=ShortViewRecipesSerializers,
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                recipes=recipe, user=user
            ).exists():
                raise ValueError('Такой рецепт уже есть')
            Favorite.objects.create(recipes=recipe, user=user)
            serializer = self.get_serializer(ShortViewRecipesSerializers(
                recipe, context={'request': request}
            ))
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favorite.objects.filter(recipes=recipe, user=user).exists():
                raise ValueError('Рецепт остутствует.')
            Favorite.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, serializer_class=ShortViewRecipesSerializers,
            methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == "POST":
            if Shopping_Cart.objects.filter(user=user,
                                            recipes=recipe).exists():
                raise ValueError(
                    'Такой рецепт уже добавлен в Ваш список покупок.'
                )
            Shopping_Cart.objects.create(user=user, recipes=recipe)
            serializer = self.get_serializer(ShortViewRecipesSerializers(
                recipes=recipe, context={'request': request}
            ))
            return Response(serializer.data, stats=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            if not Shopping_Cart.objects.filter(user=user,
                                                recipes=recipe).exists():
                raise ValueError('Такого рецепта нет.')
            Shopping_Cart.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, serializer_class=ShortViewRecipesSerializers,
            permission_classes=[IsAuthenticated, ])
    def download_shopping_cart(self, request):
        print(self.request)
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        shopping_dict = Recipes.objects.filter(
            recipes_shopping_cart_recipes__user=user
        ).values(
            'ingredients__name', 'ingredients__measurement_unit',
            'ingredients__ingredient__amount'
        ).order_by('ingredients__name')
        data = []
        shopping_list = []
        for val in shopping_dict:
            key = (f'{val["ingredients__name"]}'
                   f'({val["ingredients__measurement_unit"]})'
                   f':{ val["ingredients__ingredient__amount"]}')
            data.append(key)
        for i in data:
            shopping_list.append(f'{i} \n')
        '\n'.join(shopping_list)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=shopping_list.txt'
        return response
