import flet as ft
from router import Router


def main(page: ft.Page):
    page.title = 'Flet WB'
    page.scroll = ft.ScrollMode.ALWAYS

    page.padding = ft.Padding(
        top=30,
        bottom=30,
        left=10,
        right=10
    )

    router = Router(page, initial_route='/')

    page.add(
        router.body
    )

    page.on_route_change = router.handle_route_change
    page.update()


if __name__ == '__main__':
    ft.app(target=main)
