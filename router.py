import flet as ft

import models.sqlalchemy
import pages


class UserControl:
    def __init__(self):
        self.authorized_user = None

    def get_user(self):
        return self.authorized_user

    def set_user(self, value: models.sqlalchemy.User):
        self.authorized_user = value

    def logout(self):
        self.authorized_user = None


class Router:
    def __init__(self, page: ft.Page, initial_route: str = '/'):
        self.user_control = UserControl()

        self.routes = {
            '/': lambda: pages.Index(page, self.user_control),
            '/login': lambda: pages.Login(page, self.user_control),
            '/registration': lambda: pages.Registration(page, self.user_control),
            '/profile': lambda: pages.Profile(page, self.user_control)
        }
        self.page = page
        self.body = ft.Container(content=self.routes[initial_route]())

    def handle_route_change(self, route):
        self.body.clean()
        new_content = self.routes[route.route]()
        if not new_content:
            return

        self.body.content = new_content
        self.body.update()
