import typing
from passwords import create_hash, validate_password
import flet as ft
import controls
from models import sqlalchemy, pydantic

product = controls.Product(title='Товар 1', description='Описание товара', price=30000, quantity_left=12, id=1)
product2 = controls.Product(
    title='Банка тушенки',
    description='Ну а хули ты думал, в сказку попал?. Тут будет долгое описание того, как я сходил в шарагу посрать. Короче так посрал, че в глазах потемнело.',
    price=1_000_00,
    quantity_left=12,
    id=2,
    logo='https://avatars.mds.yandex.net/get-mpic/4409630/2a0000018af09d16f28a7d79c7217f62dd21/orig'
)


def render_error(page: ft.Page, message: str):
    """
    Функция для отображения ошибки.
    :param page: параметр ft.Page.
    :param message: Сообщение ошибки.
    :return: возвращает None
    """

    def handle_decline_banner(_):
        page.banner.open = False
        page.update()

    banner = ft.Banner(
        bgcolor=ft.colors.RED_50,
        leading=ft.Icon(ft.icons.ERROR_OUTLINED, color=ft.colors.RED, size=40),
        content=ft.Text(
            message,
            color='black'
        ),
        actions=[
            ft.TextButton("Закрыть", on_click=handle_decline_banner),
        ],
    )
    page.banner = banner
    page.banner.open = True
    page.update()


def render_warning(page: ft.Page, message: str):
    """
    Функция для отображения предупреждения.
    :param page: параметр ft.Page
    :param message: Сообщение предупреждения.
    :return: возвращает None
    """

    def handle_decline_banner(_):
        page.banner.open = False
        page.update()

    banner = ft.Banner(
        bgcolor=ft.colors.AMBER_100,
        leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=40),
        content=ft.Text(
            message
        ),
        actions=[
            ft.TextButton("Закрыть", on_click=handle_decline_banner)
        ],
    )
    page.banner = banner
    page.banner.open = True
    page.update()


def Index(page: ft.Page, user_control: typing.Any):
    search_ref = ft.Ref()
    products = sqlalchemy.Product.fetch_all(quantity_left__gt=0)
    column = ft.Column()

    authorized_user = user_control.get_user()

    def handle_navigate_to_profile(_):
        if not authorized_user:
            return page.go('/login')

        page.go('/profile')

    def handle_buy_product_now(product_clicked):
        print('buy now', product_clicked)

        if not authorized_user:
            return page.go('/login')

    def handle_add_product_to_cart(product_clicked):
        if not authorized_user:
            return page.go('/login')

        cart_item, is_created = sqlalchemy.CartItem.fetch_or_create(
            user_id=authorized_user.id,
            product_id=product_clicked.id
        )

        if not is_created:
            sqlalchemy.CartItem.update(
                row_id=cart_item.id,
                quantity=cart_item.quantity + 1
            )

        user_cart_items_length = get_total_cart_items(
            sqlalchemy.CartItem.fetch_all(
                user_id=authorized_user.id
            )
        )

        cart_button.text = f'{user_cart_items_length}'
        page.update()

    def handle_product_card_click(product_clicked):
        print('product clicked: ', product_clicked)

    def handle_search(ref: ft.Ref):
        search_string: str = ref.current.value

        product_list.products = list(filter(
            lambda product_iter: search_string.lower() in product_iter.title.lower(),
            products
        ))

    def handle_open_shopping_cart(_):
        user_cart_items = sqlalchemy.CartItem.fetch_all(
            user_id=authorized_user.id
        )

        def handle_quantity_change(cart_item: sqlalchemy.CartItem, number: int = 1):
            if cart_button:
                cart_button.text = f"{int(cart_button.text) + number}"
                page.update()

            return sqlalchemy.CartItem.update(
                row_id=cart_item.id,
                quantity=cart_item.quantity + number
            )

        def handle_cart_item_delete(cart_item: sqlalchemy.CartItem):
            return sqlalchemy.CartItem.delete(id=cart_item.id)

        drawer = controls.ShoppingCartCanvas(
            cart_items=user_cart_items,
            on_item_delete=handle_cart_item_delete,
            on_quantity_change=handle_quantity_change,
        )

        page.show_end_drawer(end_drawer=drawer)

    def get_total_cart_items(items: list[sqlalchemy.CartItem]):
        return sum([item.quantity for item in items])

    product_list = controls.ProductList(
        products=products,
        on_add_to_cart_click=handle_add_product_to_cart,
        on_buy_now_click=handle_buy_product_now,
        on_product_click=handle_product_card_click,
        products_per_page=3,
    )

    if authorized_user:
        cart_items = sqlalchemy.CartItem.fetch_all(user_id=authorized_user.id)
        cart_button = ft.Badge(
            content=ft.IconButton(
                icon=ft.icons.SHOPPING_CART,
                on_click=handle_open_shopping_cart,
            ),
            text=f'{get_total_cart_items(cart_items)}',
        )
    else:
        cart_button = None

    if authorized_user:
        profile_button = ft.Row(
            controls=[
                cart_button,
                ft.CupertinoButton(
                    content=ft.CircleAvatar(
                        foreground_image_url=authorized_user.avatar,
                        width=75,
                        content=ft.Text(authorized_user.first_name[0])
                    ),
                    on_click=handle_navigate_to_profile,
                ),
            ],
            spacing=15,
        )
    else:
        profile_button = ft.TextButton(
            text='Войти',
            on_click=handle_navigate_to_profile,
        )

    column.controls.append(
        ft.Container(content=ft.Row(
            controls=[
                ft.Image(
                    src="https://static-basket-01.wbbasket.ru/vol0/i/wb-og-win.jpg",
                    width=50,
                    border_radius=10
                ),

                ft.Row([
                        ft.TextField(
                            label='Поиск товаров',
                            width=500,
                            on_submit=lambda *_: handle_search(search_ref),
                            ref=search_ref,
                        ),
                        ft.IconButton(
                            icon=ft.icons.SEARCH,
                            on_click=lambda *_: handle_search(search_ref),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    controls=[
                        profile_button
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
            padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            margin=ft.Margin(bottom=20, left=0, right=0, top=0),
        )
    )

    if products and product_list.products:
        column.controls.append(product_list)
    else:
        column.controls.append(ft.Text('Ничего не найдено!!'))

    return column


def Login(page: ft.Page, user_control: typing.Any):
    """
    Страница авторизации пользователя в аккаунт.
    """

    authorized_user = user_control.get_user()
    if authorized_user:
        return page.go('/')

    def handle_form_submit(data: dict):
        email = data.get('email')
        password = data.get('password')

        user = sqlalchemy.User.fetch_one(email=email)
        if not user:
            return render_error(
                page=page,
                message='Данный пользователь еще не зарегистрирован.'
            )

        password_is_valid = validate_password(password, user.password_hash)
        if not password_is_valid:
            return render_error(
                page=page,
                message='Неверные данные для входа.'
            )

        user_control.set_user(user)
        page.go('/')

    def handle_registration_button_click(_):
        page.go('/registration')

    return ft.Column(
        [
            ft.Text('Авторизация', size=25, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row(
                [
                    controls.FletForm(
                        model=pydantic.UserLoginModel,
                        handle_form_submit=handle_form_submit,
                        submit_button_text='Войти',
                        actions=[
                            ft.ElevatedButton('Регистрация', on_click=handle_registration_button_click)
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )


def Registration(page: ft.Page, user_control: typing.Any):
    """
    Страница регистрации пользователя в системе.
    """

    authorized_user = user_control.get_user()
    if authorized_user:
        return page.go('/')

    def handle_form_submit(data: dict):
        password = data.pop('password')
        data['password_hash'] = create_hash(password)
        user_exists = sqlalchemy.User.fetch_one(
            email=data.get('email')
        )

        if user_exists:
            return render_error(page, 'Данный пользователь уже зарегистрирован!')

        user = sqlalchemy.User.create(**data)
        user_control.set_user(user)
        page.go('/')

    def handle_login_button_click(_):
        page.go('/login')

    return ft.Column(
        [
            ft.Text('Регистрация', size=25, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Row(
                [
                    controls.FletForm(
                        model=pydantic.UserRegisterModel,
                        handle_form_submit=handle_form_submit,
                        submit_button_text='Зарегистрироваться',
                        actions=[
                            ft.ElevatedButton('Вход', on_click=handle_login_button_click)
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )


def Profile(page: ft.Page, user_control: typing.Any):
    authorized_user = user_control.get_user()
    if not authorized_user:
        page.go('/login')
        page.update()
        return

    profile_content = controls.FletForm(
        model=pydantic.UserRegisterModel,
        initial_values={
            'email': authorized_user.email,
            'first_name': authorized_user.first_name,
            'last_name': authorized_user.last_name
        },
        submit_button_text='Изменить'
    )

    orders = sqlalchemy.Order.fetch_all(user_id=authorized_user.id)

    def handle_logout_dialog_confirm(_):
        page.dialog.open = False
        user_control.logout()
        page.go('/')

    def handle_logout_dialog_cancel(_):
        page.dialog.open = False
        page.update()

    def handle_create_product(data: dict):
        sqlalchemy.Product.create(**data)
        page.go('/')

    logout_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Выход из аккаунта"),
        content=ft.Text("Вы уверены, что хотите выйти из аккаунта?"),
        actions=[
            ft.TextButton("Да", on_click=handle_logout_dialog_confirm),
            ft.TextButton("Нет", on_click=handle_logout_dialog_cancel),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=handle_logout_dialog_cancel,
    )

    create_product_content = controls.FletForm(
        model=pydantic.ProductCreateModel,
        handle_form_submit=handle_create_product,
        submit_button_text='Создать'
    )

    order_cards = [
        controls.OrderCard(
            order=order,
            order_items=sqlalchemy.OrderItem.fetch_all(order_id=order.id)
        ) for order in orders
    ]

    orders_menu_content = ft.Column(
        controls=order_cards,
    )

    def show_logout_dialog():
        page.dialog = logout_dialog
        logout_dialog.open = True
        page.update()

    content_by_destinations = {
        "0": profile_content,
        "1": orders_menu_content,
        "2": show_logout_dialog,
        "3": create_product_content
    }

    def get_page_content(selected_index: int):
        content = content_by_destinations.get(
            str(selected_index),
            ft.Text('Ничего не найдено!')
        )

        if isinstance(content, typing.Callable):
            return content()

        menu_bar.selected_index = selected_index

        return ft.Column(
            controls=[
                content
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER
        )

    def handle_move_back(_):
        page.go('/')

    def handle_menu_bar_change(event):
        selected_index = event.data
        content = get_page_content(selected_index)
        if not content:
            return

        content_container.content = content
        page.update()

    destinations = [
        ft.NavigationRailDestination(
            icon=ft.icons.PERSON,
            selected_icon=ft.icons.PERSON_2,
            label="Ред. профиля"
        ),
        ft.NavigationRailDestination(
            icon=ft.icons.SHOPPING_CART_CHECKOUT_ROUNDED,
            selected_icon=ft.icons.SHOPPING_CART_CHECKOUT_ROUNDED,
            label="Мои заказы",
        ),
        ft.NavigationRailDestination(
            icon=ft.icons.LOGOUT,
            selected_icon=ft.icons.LOGOUT,
            label="Выход",
        ),
    ]

    if authorized_user.role == sqlalchemy.UserRoles.USER:
        destinations.append(
            ft.NavigationRailDestination(
                icon=ft.icons.CREATE_OUTLINED,
                selected_icon=ft.icons.CREATE_OUTLINED,
                label="Создать товар",
            ),
        )

    menu_bar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        leading=ft.FloatingActionButton(
            icon=ft.icons.ARROW_BACK,
            text="Назад",
            on_click=handle_move_back
        ),
        group_alignment=-0.9,
        min_width=100,
        height=500,
        min_extended_width=400,
        on_change=handle_menu_bar_change,
        destinations=destinations,
    )

    profile_bio = ft.Row(
        controls=[
            ft.CircleAvatar(
                foreground_image_url=authorized_user.avatar,
                scale=1.3,
                content=ft.Text(authorized_user.first_name[0])
            ),
            ft.Text(f'{authorized_user.first_name} {authorized_user.last_name}', size=25)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    content_container = ft.Container(
        alignment=ft.Alignment(x=50, y=50),
        margin=ft.Margin(top=30, bottom=0, left=50, right=10),
        content=get_page_content(0)
    )

    return ft.Column(
        controls=[
            profile_bio,
            ft.Row(
                controls=[
                    menu_bar,
                    content_container
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                alignment=ft.MainAxisAlignment.START
            )
        ]
    )
