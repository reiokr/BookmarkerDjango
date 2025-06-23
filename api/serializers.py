from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Bm, Bml, CustomUser, UserOptions


class UserOptionsSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = UserOptions
        fields = ('theme', 'localization', 'settings', 'owner',)

    def create(self, validated_data):
        options = UserOptions.objects.create(**validated_data)
        return options

    def update(self, instance, validated_data):
        instance.theme = validated_data.get('theme', instance.theme)
        instance.localization = validated_data.get(
            'localization', instance.localization)
        instance.settings = validated_data.get('settings', instance.settings)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    bookmarks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Bm.objects.all())
    bookmark_link = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Bml.objects.all())
    options = UserOptionsSerializer(many=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'last_login', 'is_staff', 'is_active', 'is_superuser',
                  'email', 'date_joined', 'date_updated', 'categories', 'bookmarks', 'bookmark_link', 'options',)


class CategorySerializer(serializers.Serializer):
    categories = serializers.ListField(
        child=serializers.CharField(), allow_empty=True)

    def create(self, validated_data):
        return CustomUser.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.categories = validated_data.get(
            'categories', instance.categories)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user = CustomUser.objects.filter(email=attrs.get('email')).first()
        if user:
            if user.is_active:
                return super().validate(attrs)
            else:
                return {'email': 'not_verified', 'msg': _('Email not verified'), 'status': 403}
        else:
            return {'email': 'not_registered', 'msg': 'This email does not exist', 'status': 401}

    def get_token(cls, user):
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        # Add custom claims
        # token['email'] = user.email
        # ...
        return token


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('password', 'password2',
                  'email',)
        # extra_kwargs = {
        #     'first_name': {'required': False},
        #     'last_name': {'required': False}
        # }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            # username=validated_data['username'],
            email=validated_data['email'],
            # first_name=validated_data['first_name'],
            # last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class BmSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Bm
        fields = ['id', 'title', 'category', 'bm_type', 'description', 'thumbnails', 'url', 'video_id', 'list_id', 'list_index','list_items_count', 'channel_id', 'channel_title', 'start_at',
                  'keywords', 'length', 'view_count', 'like_count', 'comment_count', 'privacy_status', 'publish_date', 'original_category', 'created_at', 'updated_at', 'owner']


class BmlSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Bml
        fields = ['id', 'title', 'category', 'bm_type',
                  'description', 'image_url', 'url', 'created_at', 'owner']

    def create(self, validated_data):
        bml = Bml.objects.create(**validated_data)
        return bml

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.title = validated_data.get(
            'title', instance.title)
        instance.category = validated_data.get('category', instance.category)
        instance.bm_type = validated_data.get('bm_type', instance.bm_type)
        instance.description = validated_data.get(
            'description', instance.description)
        instance.image_url = validated_data.get(
            'image_url', instance.image_url)
        instance.url = validated_data.get('url', instance.url)
        instance.created_at = validated_data.get(
            'created_at', instance.created_at)
        instance.owner = validated_data.get('owner', instance.owner)

        instance.save()
        return instance
