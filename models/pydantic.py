import re

import pydantic
from typing import Optional, Union
from datetime import datetime
from . import sqlalchemy


class MessageConfig:
    error_msg_templates = {
        'int_parsing': 'Значение должно быть целым числом.',
        'float_parsing': 'Значение должно быть числом с плавающей точкой.',
        'str_parsing': 'Значение должно быть в текстовом виде.'
    }


class PydanticModel(pydantic.BaseModel, extra=pydantic.Extra.ignore):
    """
    Базовая модель Pydantic
    """


class UserLoginModel(PydanticModel):
    """
    Модель для авторизации пользователя
    """

    email: str = pydantic.Field(
        title='Эл. почта',
    )

    password: str = pydantic.Field(
        title='Пароль',
    )

    @pydantic.field_validator('email')
    def validate_email(cls, value: str):
        if len(value) < 5:
            raise ValueError(
                'Поле почты должно состоять не менее чем из 5 символов.'
            )

        elif not re.match(
            pattern=r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+',
            string=value
        ):
            raise ValueError(
                'Неверный формат эл.почты.'
            )

        return value


class UserRegisterModel(PydanticModel):
    """
    Модель для регистрации пользователя
    """

    email: str = pydantic.Field(
        title='Эл. почта',
        description='Ваша эл.почта для регистрации аккаунта',
        serialization_alias='email',
        validation_alias=pydantic.AliasChoices('email')
    )

    password: str = pydantic.Field(
        title='Пароль',
        serialization_alias='password',
        validation_alias=pydantic.AliasChoices('password')
    )

    first_name: str = pydantic.Field(
        title='Имя',
        serialization_alias='firstName',
        validation_alias=pydantic.AliasChoices('firstName', 'first_name')
    )

    last_name: str = pydantic.Field(
        title='Фамилия',
        default='',
        serialization_alias='lastName',
        validation_alias=pydantic.AliasChoices('lastName', 'last_name')
    )

    @pydantic.field_validator('email')
    def validate_email(cls, value: str):
        if len(value) < 5:
            raise ValueError(
                'Поле почты должно состоять не менее чем из 5 символов.'
            )

        elif not re.match(
                pattern=r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+',
                string=value
        ):
            raise ValueError(
                'Неверный формат эл.почты.'
            )

        return value

    @pydantic.field_validator('password')
    def validate_password(cls, value: str):
        if len(value) < 8:
            raise ValueError(
                'Пароль должен состоять минимум из 8 символов!'
            )

        return value


class UserModel(PydanticModel):
    """
    Модель для регистрации пользователя
    """

    id: Optional[int] = pydantic.Field(
        description='ID пользователя',
        serialization_alias='id',
        validation_alias=pydantic.AliasChoices('id')
    )

    email: str = pydantic.Field(
        description='Эл. почта пользователя',
        serialization_alias='email',
        validation_alias=pydantic.AliasChoices('email')
    )

    password_hash: str = pydantic.Field(
        description='Хэш пароля пользователя',
        serialization_alias='passwordHash',
        validation_alias=pydantic.AliasChoices('passwordHash', 'password_hash')
    )

    first_name: str = pydantic.Field(
        description='Имя пользователя',
        serialization_alias='firstName',
        validation_alias=pydantic.AliasChoices('firstName', 'first_name')
    )

    last_name: Optional[str] = pydantic.Field(
        description='Фамилия пользователя',
        default=None,
        serialization_alias='lastName',
        validation_alias=pydantic.AliasChoices('lastName', 'last_name')
    )

    date_joined: Optional[Union[datetime, str]] = pydantic.Field(
        description='Дата регистрации пользователя',
        serialization_alias='dateJoined',
        default_factory=datetime.now,
        validation_alias=pydantic.AliasChoices('dateJoined', 'date_joined')
    )

    role: sqlalchemy.UserRoles = pydantic.Field(
        description='Роль пользователя',
        default=sqlalchemy.UserRoles.USER,
        serialization_alias='role',
        validation_alias=pydantic.AliasChoices('role')
    )


class ProductModel(PydanticModel):
    """
    Модель для валидации товара
    """

    id: Optional[int] = pydantic.Field(
        title='ID товара',
        serialization_alias='id',
        validation_alias=pydantic.AliasChoices('id')
    )

    title: str = pydantic.Field(
        title='Заголовок',
        serialization_alias='title',
        validation_alias='title',
    )

    description: str = pydantic.Field(
        title='Описание',
        serialization_alias='description',
        validation_alias='description',
    )

    price: int = pydantic.Field(
        title='Цена',
        serialization_alias='price',
        validation_alias='price',
    )

    quantity_left: int = pydantic.Field(
        title='Кол-во на складе',
        serialization_alias='quantityLeft',
        validation_alias=pydantic.AliasChoices('quantityLeft', 'quantity_left'),
    )

    logo: Union[str, None] = pydantic.Field(
        title='Фото',
        serialization_alias='logo',
        validation_alias='logo',
        default=None
    )

    @pydantic.field_validator('quantity_left')
    def validate_quantity_left(cls, value: int):
        if value < 0:
            raise ValueError(
                'Значение кол-во оставшегося товара должно быть больше нуля.'
            )

        return value

    @pydantic.field_validator('price')
    def validate_quantity_left(cls, value: int):
        if value < 0:
            raise ValueError(
                'Значение цены товара должно быть больше нуля.'
            )

        return value


class ProductCreateModel(PydanticModel):
    """
    Модель для валидации товара
    """

    title: str = pydantic.Field(
        title='Заголовок',
        serialization_alias='title',
        validation_alias='title',
    )

    description: str = pydantic.Field(
        title='Описание',
        serialization_alias='description',
        validation_alias='description',
    )

    price: int = pydantic.Field(
        title='Цена',
        serialization_alias='price',
        validation_alias='price',
    )

    quantity_left: int = pydantic.Field(
        title='Кол-во на складе',
        serialization_alias='quantityLeft',
        validation_alias=pydantic.AliasChoices('quantityLeft', 'quantity_left'),
    )

    logo: Union[str, None] = pydantic.Field(
        title='Фото (ссылка)',
        serialization_alias='logo',
        validation_alias='logo',
    )

    @pydantic.field_validator('quantity_left')
    def validate_quantity_left(cls, value: int):
        if value < 0:
            raise ValueError(
                'Значение кол-во оставшегося товара должно быть больше нуля.'
            )

        return value

    @pydantic.field_validator('price')
    def validate_price(cls, value: int):
        if value < 0:
            raise ValueError(
                'Значение цены товара должно быть больше нуля.'
            )

        return value * 100
