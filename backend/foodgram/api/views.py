from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import exceptions, status, viewsets
from rest_framework import filters
# from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers


from .filters import CustomFilters
from .pagination import CustomPaginator
from .permissions import AuthorOnly, AuthorOrReadOnly
from .serializers import (
    CreateUpdateRecipesSerializer,
    CustomUserSerializer,
    GetRecipesSerializer,
    IngredientSerializer,
    ShortViewRecipesSerializer,
    SubscriptionSerializer,
    TagSerializer
)
from recipes.models import (
    Tag,
    Recipes,
    Ingredient,
    Shopping_Cart,
    Favorite
)
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action(detail=False,
            serializer_class=SubscriptionSerializer, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        if user.is_anonymous:
            raise serializers.ValidationError(
                'Вы неавторизованы. Авторизуйтесь'
            )
        query = User.objects.filter(subscribe__user=user)
        serializer = SubscriptionSerializer(query, many=True,
                                            context={'request': request})
        page = self.paginate_queryset(query)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(serializer_class=SubscriptionSerializer,
            methods=['post', 'delete'],
            permission_classes=[AuthorOnly, ], detail=True)
    def subscribe(self, request, id):
        if request.method == "POST":
            user = request.user
            author = get_object_or_404(User, id=id)
            if Subscription.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError('подписка уже оформлена')
            Subscription.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        author = get_object_or_404(User, id=id)
        user = request.user
        subscribe = get_object_or_404(Subscription, user=user,
                                      author=author)
        # subscribe = Subscription.objects.filter(user=user, author=author)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name', )
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomFilters
    pagination_class = CustomPaginator
    permission_classes = [AuthorOrReadOnly, ]

    def list(self, request, queryset=queryset, *args, **kwargs):
        user = self.request.user.id
        serializer = self.get_serializer(queryset, many=True)
        if user is None and (
            queryset == queryset.filter(
                recipes_favorite_recipes__user=user
            )
            or queryset == queryset.filter(
                recipes_shopping_cart_recipes__user=user
            )
        ):
  
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GetRecipesSerializer
        return CreateUpdateRecipesSerializer

    def perform_create(self, serializer):
        author = self.request.user
        if serializer.is_valid(raise_exception=True):
            serializer.save(author=author)

    @action(detail=True, methods=['post', 'delete'],
            serializer_class=ShortViewRecipesSerializer,
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                recipes=recipe, user=user
            ).exists():
                raise serializers.ValidationError(
                    'Такоу рецепт уже существует'
                )
            Favorite.objects.create(recipes=recipe, user=user)
            serializer = ShortViewRecipesSerializer(
                recipe, context={'request': request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if Favorite.objects.filter(recipes=recipe, user=user).exists():
            Favorite.objects.filter(recipes=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, serializer_class=ShortViewRecipesSerializer,
            methods=['post', 'delete'], permission_classes=[AuthorOnly])
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == "POST":
            if Shopping_Cart.objects.filter(user=user,
                                            recipes=recipe).exists():
                raise serializers.ValidationError(
                    'Такой рецепт уже добавлен в Ваш список покупок.'
                )
            Shopping_Cart.objects.create(user=user, recipes=recipe)
            serializer = ShortViewRecipesSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if Shopping_Cart.objects.filter(user=user,
                                        recipes=recipe).exists():
            Shopping_Cart.objects.filter(recipes=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, serializer_class=ShortViewRecipesSerializer,
            permission_classes=[IsAuthenticated, ], methods=['GET'])
    def download_shopping_cart(self, request):
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        shopping_dict = Recipes.objects.filter(
            recipes_shopping_cart_recipes__user=user
        ).values(
            'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(ingredient_amount=Sum('recipe__amount'))
        # ).annotate(ingredient_amount=Sum('ingredients__ingredient__amount'))
        data = {}
        shopping_list = []
        for val in shopping_dict:
            key = (f'{val["ingredients__name"]}',
                   f'{val["ingredients__measurement_unit"]}')
            data[key] = val["ingredient_amount"]
        for key, val in data.items():
            shopping_list.append(f'{key}:{val} \n')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename= {0}'.format('shopping_list.txt')
        )
        return response
