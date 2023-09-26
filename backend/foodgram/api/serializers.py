import base64

from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer
# from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (
    Amount,
    Tag,
    Ingredient,
    Recipes,
    Favorite,
    Shopping_Cart
)

from users.models import User, Subscription


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CreateUserSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']


class CustomUserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()
    username = serializers.CharField(
        max_length=100,
        required=False,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z'),
                    UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ('username',
                  'first_name',
                  'last_name',
                  'email',
                  'id',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class ShortViewRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipes
        fields = ('name', 'cooking_time', 'image', 'id')


class SubscriptionSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(read_only=True)
    email = serializers.StringRelatedField(read_only=True)
    first_name = serializers.StringRelatedField(read_only=True)
    last_name = serializers.StringRelatedField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = Subscription
        fields = ('username',
                  'first_name',
                  'last_name',
                  'email',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',
                  'id',)

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortViewRecipesSerializer(
            recipes,
            context={'request': request},
            many=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def validated_is_subscribed(self, value):
        user = self.context['request'].user
        if user == value:
            return ValueError('на себя подписываться нельзя')
        return value
    
    def validate(self, data):
        user = self.context['request'].user
        if user.is_anonymous:
            raise serializers.ValidationError(
                'Неавторизованный пользователь не может просматривать'
                'подписки. Авторизуйтесь.'
            )
        return data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'color', 'slug', "name")


class AmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient.id',
                                            queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Amount
        fields = ('id', 'amount', 'measurement_unit', 'name')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Количество ингредиентов не может быть отрицательным"
            )
        if value > 1000:
            raise serializers.ValidationError(
                'Слишком большое количество ингредиента в рецепте.'
                'Проверьте правильность заполнения поля "количество"'
            )
        return value


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class GetRecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = AmountSerializer(many=True, read_only=True,
                                   source='recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = ('author',
                  'image',
                  'ingredients',
                  'name',
                  'text',
                  'cooking_time',
                  'pub_date',
                  'tags',
                  "id",
                  'is_favorited',
                  'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipes=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Shopping_Cart.objects.filter(user=user, recipes=obj).exists()


class CreateUpdateRecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    ingredients = AmountSerializer(many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_in_shopping_cart',
                  'is_favorited',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError('Картинка должна быть в рецепте')
        return value

    def validated(self, data):
        for field in ('image', 'name', 'text', 'cooking_time'):
            if field is None in data:
                raise serializers.ValidationError(
                    f'{field} поле не может быть пустым'
                )
        return data

    def validate_ingredients(self, value):
        if value is None:
            raise serializers.ValidationError(
                'В рецепте должен быть хоть один ингредиент'
            )
        ingredient_list = []
        for ingredient in value:
            ingredient_list.append(ingredient)
            if ingredient_list.count(ingredient) > 1:
                raise serializers.ValidationError(
                    'В рецепте не может быть одинаковых ингредиентов'
                )
        return value

    def validate_tags(self, value):
        if value is None:
            raise serializers.ValidationError(
                'В рецепте get быть хоть 1 тэг'
            )
        tags_list = []
        for tag in value:
            tags_list.append(tag)
            if tags_list.count(tag) > 1:
                raise serializers.ValidationError(
                    'В рецепте не может быть одинаковых тэгов'
                )
        return value

    def create_ingredients_amount(self, ingredients, recipe):
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = Ingredient.objects.get(
                pk=ingredient['ingredient']['id'].id
            )
            new = Amount.objects.create(ingredient=ingredient,
                                        amount=amount,
                                        recipe=recipe)
        return new

    def create(self, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = validated_data.pop('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Ошибка: нет ингредиентов'
            )
        recipe = Recipes.objects.create(**validated_data)
        if not tags:
            raise serializers.ValidationError(
                'Ошибка: нет тэгов в рецепте'
            )
        for i in tags:
            if not Tag.objects.filter(id=i).exists():
                raise serializers.ValidationError(
                    'такого тэга нет.'
                )
        recipe.tags.set(tags)
        self.create_ingredients_amount(recipe=recipe,
                                       ingredients=ingredients)
        return recipe

    def to_representation(self, instance):
        return GetRecipesSerializer(
            instance, context={'request': self.context.get('request')}).data

    def update(self, instance, validated_data):
        tags = self.initial_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        if ingredients is not None:
            instance.ingredients.clear()
            self.create_ingredients_amount(ingredients, instance)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()
        return super().update(instance, validated_data)

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Shopping_Cart.objects.filter(user=user, recipes=obj).exists()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipes=obj).exists()