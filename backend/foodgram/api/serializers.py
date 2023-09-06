import base64
import webcolors
from rest_framework import serializers
from django.core.files.base import ContentFile

from django.core.validators import (
    RegexValidator
)
from rest_framework.validators import UniqueValidator
from djoser.serializers import UserCreateSerializer
from recipes.models import (
    Amount,
    Tag,
    Ingredient,
    Recipes,
    Favorite,
    Shopping_Cart,
)

from users.models import User, Subscription


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


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


class ShortViewRecipesSerializers(serializers.ModelSerializer):

    class Meta:
        model = Recipes
        fields = ('name', 'cooking_time', 'image', 'id')


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers. ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = Subscription
        fields = ('email',
                  'username',
                  'first_name',
                  'last_name',
                  'recipes',
                  'recipes_count',
                  'is_subscribed',
                  'id',)

    def get_recipes(self, obj):
        recipes = Recipes.objects.filter(author=obj)
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShortViewRecipesSerializers(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.author.count()

    def validated_is_subscribed(self, value):
        user = self.context['request'].user
        if user == value:
            return ValueError('на себя подписываться нельзя')
        return value


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class GetRecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='slug'
    )
    ingredients = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Recipes
        fields = ('author',
                  'image',
                  'ingredients',
                  'name',
                  'text',
                  'cooking_time',
                  'pub_date',
                  'tags')


class AmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient.id',
                                            queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Amount
        fields = ('id', 'amount', 'name', 'measurement_unit')


class CreateUpdateRecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
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

    def validated(self, data):
        for field in ('image', 'name', 'text', 'cooking_time'):
            if field is None in data:
                raise serializers.ValidationError('Поле не может быть пустым')
        return data

    def validated_ingredients(self, value):
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
                'В рецепте должен быть хоть 1 тэг'
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
            new = Amount.objects.create(
                ingredient=ingredient,
                amount=amount,
                recipe=recipe
            )
        return new

    def create(self, validated_data):
        author = self.context['request'].user
        tags = self.initial_data.get('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.update_or_create(
            author=author, **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients_amount(recipe=recipe,
                                       ingredients=ingredients)
        return recipe

    def to_representation(self, instance):
        return GetRecipesSerializer(
            instance, context={'request': self.context.get('request')}).data

    def update(self, instance, validated_data):
        print(instance)
        print(validated_data)
        tags = self.initial_data.pop('tags')
        if tags is not None:
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
