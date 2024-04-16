import dataclasses
import datetime
import os.path
import random
import typing
import base64
import flet as ft
import pydantic as pd
import pydantic_core
import qrcode
from jinja2 import Template
import settings
from models import sqlalchemy, pydantic
from io import BytesIO
import pdfkit


@dataclasses.dataclass
class Product:
    id: int
    title: str
    description: str
    price: int
    quantity_left: int
    logo: str = None
    images: list[str] = None


@dataclasses.dataclass
class CartItem:
    id: int
    product: sqlalchemy.Product
    quantity: int
    user: sqlalchemy.User


class ProductCard(ft.UserControl):
    """
    Виджет карточки товара
    """

    def __init__(
            self,
            product: Product,
            on_add_to_cart_click: typing.Callable[[Product], typing.Any] = None,
            on_buy_now_click: typing.Callable[[Product], typing.Any] = None,
            on_click: typing.Callable[[Product], typing.Any] = None
    ):
        super().__init__()
        self.__default_image_path = 'https://avatars.mds.yandex.net/get-mpic/5253116/2a0000018aa507311f34ae5b644286e1650d/orig'
        self.__product = product
        self.__on_add_to_card_click = on_add_to_cart_click
        self.__on_buy_now_click = on_buy_now_click
        self.__on_click = on_click

    def build(self):
        return ft.Container(
            on_click=lambda *_: self.__on_click and self.__on_click(self.__product),
            expand=True,
            col={'sm': 6, 'xs': 4},
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Image(
                                src=self.__product.logo or self.__default_image_path,
                                fit=ft.ImageFit.CONTAIN,
                                border_radius=25,
                                width=300
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.ListTile(
                        title=ft.Text(self.__product.title, size=22),
                        subtitle=ft.Text(
                            self.__product.description,
                            size=14,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        content_padding=0
                    ),

                    ft.Divider(),

                    ft.Row(
                        [
                            ft.Row([
                                ft.Text(
                                    f'{self.__product.price / 100} RUB',
                                    size=18,
                                    max_lines=1
                                )
                            ]),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.ADD_SHOPPING_CART,
                                    on_click=lambda *_: self.__on_add_to_card_click(self.__product),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.CURRENCY_RUBLE_OUTLINED,
                                    on_click=lambda *_: self.__on_add_to_card_click(self.__product),
                                )
                            ]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                ],
            ),
            width=400,
            padding=20,
            border_radius=20,
        )


class ProductList(ft.UserControl):
    """
    Виджет списка продуктов
    """

    def __init__(
            self,
            products: list[Product],
            on_add_to_cart_click: typing.Callable[[Product], typing.Any] = None,
            on_buy_now_click: typing.Callable[[Product], typing.Any] = None,
            on_product_click: typing.Callable[[Product], typing.Any] = None,
            products_per_page: int = 10,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.__page = 0
        self.__products = products
        self.__on_add_to_card_click = on_add_to_cart_click
        self.__on_buy_now_click = on_buy_now_click
        self.__on_product_click = on_product_click
        self.__products_per_page = products_per_page

        self.row = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
        )

    def handle_go_to_next_page(self, _):
        self.__page += 1

        products, has_next_page = self.get_elements_for_page(self.__page)

        self.row.controls = [
            ProductCard(
                product=product,
                on_buy_now_click=self.__on_buy_now_click,
                on_click=self.__on_product_click,
                on_add_to_cart_click=self.__on_add_to_card_click,
            ) for product in products
        ]

        if has_next_page:
            self.row.controls.append(
                ft.ResponsiveRow(
                    controls=[
                        ft.ElevatedButton('Загрузить еще', on_click=self.handle_go_to_next_page)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )

        self.update()

    def build(self):
        products, has_next_page = self.get_elements_for_page(self.__page)

        self.row.controls = [
            ProductCard(
                product=product,
                on_click=self.__on_product_click,
                on_buy_now_click=self.__on_buy_now_click,
                on_add_to_cart_click=self.__on_add_to_card_click,
            ) for product in products
        ]

        if has_next_page:
            self.row.controls.append(
                ft.ResponsiveRow(
                    controls=[
                        ft.ElevatedButton('Загрузить еще', on_click=self.handle_go_to_next_page)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )

            )

        return self.row

    def get_elements_for_page(self, page: int) -> [list, bool]:
        products_sliced = self.__products[0:self.__products_per_page * (page + 1)]
        return products_sliced, len(self.__products) > len(products_sliced)

    @property
    def products(self):
        return self.__products

    @products.setter
    def products(self, value: list[Product]):
        self.__products = value.copy()
        self.__page = 0

        products, has_next_page = self.get_elements_for_page(self.__page)

        self.row.controls = [
            ProductCard(
                product=product,
                on_click=self.__on_product_click,
                on_buy_now_click=self.__on_buy_now_click,
                on_add_to_cart_click=self.__on_add_to_card_click,
            ) for product in products
        ]

        if has_next_page:
            self.row.controls.append(
                ft.ResponsiveRow(
                    controls=[
                        ft.ElevatedButton('Загрузить еще', on_click=self.handle_go_to_next_page)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )

            )

        self.update()


class FletForm(ft.UserControl):
    """
    Виджет формы, адаптирующийся почти под любую модель pydantic.
    """

    def __init__(
            self,
            model: pydantic.PydanticModel,
            handle_form_submit: typing.Callable[[dict], typing.Any] = None,
            submit_button_text: str = 'Ввести',
            actions: list[ft.Control] = None,
            initial_values: dict = None,
            **kwargs
    ):

        self.__model = model
        self.__handle_form_submit = handle_form_submit
        self.__submit_button_text = submit_button_text
        self.__actions = actions

        self.__values = {}
        self.__fields = {}
        self.__initial_values = initial_values or {}
        self.container = ft.Column()

        super().__init__(**kwargs)

    @staticmethod
    def get_keyboard_type(field_name: str, field: pd.fields.FieldInfo):
        if field_name == 'email':
            return ft.KeyboardType.EMAIL

        elif field_name.startswith('password'):
            return ft.KeyboardType.VISIBLE_PASSWORD

        elif field.annotation in [str, typing.Optional[str]]:
            return ft.KeyboardType.TEXT

        elif field.annotation in (int, float, typing.Optional[int], typing.Optional[float], typing.Union[int, float]):
            return ft.KeyboardType.NUMBER

        elif field.annotation == datetime.datetime:
            return ft.KeyboardType.DATETIME

        return None

    @staticmethod
    def get_error_for_field(errors: list, field_name: str):
        result = list(filter(
            lambda error: field_name in error['loc'],
            errors
        ))

        if not result:
            return None

        return result[0]

    def handle_field_errors(self, validation_error: pd.ValidationError):
        errors = validation_error.errors()

        for field_name, field in self.__fields.items():
            if not field.value and field.data.get('required'):
                field.error_text = 'Данное поле обязательно для заполнения.'
                continue

            error = self.get_error_for_field(errors, field_name)
            if not error:
                continue

            print(error)
            error_message = error.get('ctx', {}).get('error', None) or error.get('msg')
            if not error_message:
                continue

            message = str(error_message)
            field.error_text = message

        self.update()

    def clear_field_errors(self):
        for _, field in self.__fields.items():
            field.error_text = None

        self.update()

    def handle_field_change(self, e, field_name: str):
        self.__values[field_name] = e.control.value

        if e.control.error_text:
            e.control.error_text = ''
            self.update()

    def handle_form_submit(self, _):
        try:
            self.clear_field_errors()
            self.__model.model_validate(self.__values)

            if self.__handle_form_submit:
                return self.__handle_form_submit(self.__values.copy())
        except pd.ValidationError as validation_error:
            self.handle_field_errors(validation_error)

    def build(self):
        fields = self.__model.__fields__

        if self.container.controls:
            self.container.controls = []

        for field_name, field in fields.items():
            keyboard_type = self.get_keyboard_type(field_name, field)
            if not keyboard_type:
                continue

            initial_value = self.__initial_values.get(field_name, '')
            if initial_value:
                self.__values[field_name] = initial_value
            else:
                default_value = field.get_default(call_default_factory=True)
                if not isinstance(default_value, pydantic_core.PydanticUndefinedType):
                    self.__values[field_name] = default_value
                else:
                    self.__values[field_name] = ''

            is_required = field.is_required()

            self.container.controls.append(
                ft.Row([
                    field := ft.TextField(
                        suffix_text='*' if is_required else None,
                        suffix_style=ft.TextStyle(color='red'),
                        label=field.title,
                        value=self.__values[field_name],
                        tooltip=field.description,
                        keyboard_type=keyboard_type,
                        on_change=lambda e, fn=field_name: self.handle_field_change(e, fn),
                        password=keyboard_type is ft.KeyboardType.VISIBLE_PASSWORD,
                        can_reveal_password=keyboard_type is ft.KeyboardType.VISIBLE_PASSWORD,
                        data={
                            'required': is_required
                        }
                    )
                ])
            )

            self.__fields[field_name] = field

        if not self.__actions:
            self.__actions = []

        actions = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text=self.__submit_button_text,
                    on_click=self.handle_form_submit
                ),
                *self.__actions
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        self.container.controls.append(actions)
        return self.container


class ShoppingCartCanvas(ft.NavigationDrawer):
    """
    Выдвижное меню корзины
    """

    def __init__(
            self,
            cart_items: list[sqlalchemy.CartItem],
            on_quantity_change: typing.Callable[[sqlalchemy.CartItem, int], typing.Any] = None,
            on_item_delete: typing.Callable[[sqlalchemy.CartItem], typing.Any] = None,
            **kwargs,
    ):
        self.__cart_items = cart_items
        self.__on_quantity_change = on_quantity_change
        self.__on_item_delete = on_item_delete
        self.drawer_heading = [
            ft.Row(
                controls=[
                    ft.Text(
                        value='Корзина',
                        size=25,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Divider(),
        ]

        super().__init__(**kwargs)

    def find_cart_item(self, cart_item: sqlalchemy.CartItem):
        cart_items = self.__cart_items
        items_found = list(filter(lambda item: item.id == cart_item.id, cart_items))
        if not items_found:
            return None, cart_items

        item_index = cart_items.index(items_found[0])
        return cart_items[item_index], cart_items

    def handle_quantity_change(self, cart_item: sqlalchemy.CartItem, number: int = 1):
        item_found, cart_items = self.find_cart_item(cart_item)
        if not item_found:
            return

        new_quantity = item_found.quantity + number
        if new_quantity <= 0:
            return self.handle_item_delete(cart_item)

        item_found.quantity = new_quantity
        self.cart_items = cart_items

        if self.__on_quantity_change:
            self.__on_quantity_change(cart_item, number)

    def handle_item_delete(self, cart_item: sqlalchemy.CartItem):
        item_found, cart_items = self.find_cart_item(cart_item)
        if not item_found:
            return

        cart_items.remove(item_found)
        self.cart_items = cart_items

        if self.__on_item_delete:
            self.__on_item_delete(cart_item)

    def render_cart_items(self, cart_items: list[CartItem]):
        return [
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    foreground_image_url=item.product.logo,
                                    content=ft.Text(item.product.title[0]),
                                    scale=1.3
                                ),
                                ft.Row(
                                    controls=[
                                        ft.TextButton(
                                            text='+',
                                            on_click=lambda *_, cart_item=item:
                                                self.handle_quantity_change(cart_item, 1),
                                        ),

                                        ft.Text(
                                            value=f'{item.quantity}'
                                        ),

                                        ft.TextButton(
                                            text='-',
                                            on_click=lambda *_, cart_item=item:
                                                self.handle_quantity_change(cart_item, -1),
                                        ),
                                    ],
                                    spacing=5
                                ),

                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color='red',
                                    on_click=lambda *_, cart_item=item:
                                        self.handle_item_delete(cart_item)
                                )
                            ]
                        ),
                        height=75,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ) for item in cart_items
        ]

    @property
    def cart_items(self):
        return self.__cart_items.copy()

    @cart_items.setter
    def cart_items(self, value: list[CartItem]):
        self.__cart_items = value.copy()

        drawer_items = self.render_cart_items(value.copy())

        self.controls = [
            *self.drawer_heading,
            *drawer_items
        ]

        if not drawer_items:
            self.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            '* корзина пуста *',
                            size=10,
                            color='grey'
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )

        self.update()

    def build(self):
        drawer_items = self.render_cart_items(cart_items=self.__cart_items)

        self.controls = [
            *self.drawer_heading,
            *drawer_items
        ]

        if not drawer_items:
            self.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            '* корзина пуста *',
                            size=10,
                            color='grey'
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )

        return super().build()

    def on_dismiss(self):
        self.cart_items = []
        self.clean()


class OrderCard(ft.UserControl):
    """
    Виджет карточки заказа
    """

    def __init__(
            self,
            order: sqlalchemy.Order,
            order_items: list[sqlalchemy.OrderItem],
            **kwargs
    ):
        super().__init__(**kwargs)

        self.__order = order
        self.__order_items = order_items
        self.__default_image_path = 'https://avatars.mds.yandex.net/get-mpic/5253116/2a0000018aa507311f34ae5b644286e1650d/orig'

    def generate_qr_code(self):
        qr_code = qrcode.make(
            data='mailto:software.dev1988@mail.com'
        )
        buffer = BytesIO()
        qr_code.save(buffer)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def get_total_quantity(self):
        return sum([item.quantity for item in self.__order_items])

    def download_request(self, _):
        filename = f'order_{self.__order.id}.pdf'
        path = os.path.join(settings.MEDIA_DIR, filename)

        with open('example.html', encoding='utf-8') as file:
            template = Template(source=file.read())

        response = template.render(
            order=self.__order,
            order_items=self.__order_items,
            round=round,
            code=random.randint(100, 999),
            total_amount=self.get_total_quantity(),
        )

        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
        pdfkit.from_string(response, path, configuration=config)

        return self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text('Файл сохранен'),
                content=ft.Text(
                    f'Файл сохранен в {path}.'
                )
            )
        )

    def build(self):
        qr_code_image = self.generate_qr_code()

        qr_code = ft.Row(
            controls=[
                ft.Image(
                    src_base64=qr_code_image,
                    width=300,
                    border_radius=10,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        images_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=item.product.logo or self.__default_image_path,
                        width=50,
                        border_radius=5,
                    ) for item in self.__order_items
                ],
                spacing=10,
                scroll=ft.ScrollMode.ADAPTIVE,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.Padding(
                top=20,
                bottom=20,
                left=0,
                right=0
            )
        )

        footer_row = ft.Row(
            controls=[
                ft.Text(
                    f'{round(self.__order.total_price / 100, 2)} RUB',
                    size=24,
                ),
                ft.IconButton(
                    icon=ft.icons.PRINT,
                    on_click=self.download_request
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        tiles_row = ft.Row(
            controls=[
                ft.ListTile(
                    leading=ft.Icon(ft.icons.LOCAL_SHIPPING),
                    title=ft.Text("3 дня"),
                    dense=True,
                    width=160
                ),

                ft.ListTile(
                    leading=ft.Icon(ft.icons.DELIVERY_DINING),
                    title=ft.Text("Доставка"),
                    dense=True,
                    width=160
                ),
            ],
            wrap=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=0
        )

        return ft.Container(
            border_radius=20,
            bgcolor=ft.colors.BLACK12,
            content=ft.Column(
                controls=[
                    qr_code,
                    images_row,
                    tiles_row,
                    ft.Divider(),
                    footer_row,
                ],
                spacing=10,
                expand=True,
            ),
            width=400,
            padding=20,
            expand=True,
        )