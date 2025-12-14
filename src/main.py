import threading
from itertools import islice
from typing import Callable, Optional

import flet as ft

from flaskrclient import BlogPost, FlaskrClient

semaphore = threading.Semaphore()


class PostView(ft.Column):
    def __init__(
        self,
        post: BlogPost,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
    ):
        super().__init__()
        self.post = post
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.title = ft.Text(
            self.post.title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM
        )
        self.subtitle = ft.Text(
            f"by {self.post.author} on {self.post.created}",
            theme_style=ft.TextThemeStyle.LABEL_SMALL,
        )
        self.body = ft.Text(self.post.body)
        interaction_buttons = ft.Row()
        if self.on_edit:
            interaction_buttons.controls.append(
                ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e: self.on_edit(self))
            )
        if self.on_delete:
            interaction_buttons.controls.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_300,
                    on_click=lambda e: self.on_delete(self),
                )
            )
        self.controls = [
            ft.Row(controls=[self.title, interaction_buttons]),
            self.subtitle,
            self.body,
            ft.Divider(),
        ]

    def update(self):
        self.title.value = self.post.title
        self.body.value = self.post.body
        super().update()


class FlaskrApp(ft.Column):
    def __init__(self, client: FlaskrClient):
        super().__init__()
        self.client = client
        self.username = ""
        self.user_info = ft.Text()
        self.new_post_button = ft.ElevatedButton(
            text="New Post", on_click=self.new_post, disabled=True
        )
        self.expand = True
        self.posts_list_view = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
            on_scroll=self.load_posts_on_scroll,
            expand=True,
        )
        self.posts_iterator = []
        self.controls = [
            ft.Row(
                controls=[
                    self.user_info,
                    ft.Text(
                        value="FlaskR Blog",
                        theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.REFRESH, on_click=lambda e: self.refresh()
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS, on_click=self.enter_creds
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            self.new_post_button,
            self.posts_list_view,
        ]

    def refresh(self):
        self.posts_iterator = self.client.posts()
        self.load_more_posts()
        self.load_more_posts()

    def load_more_posts(self):
        batch = list(islice(self.posts_iterator, 15))

        if not batch:
            return False

        for post in batch:
            if self.client.authenticated and self.username == post.author:
                self.posts_list_view.controls.append(
                    PostView(
                        post=post, on_edit=self.edit_post, on_delete=self.delete_post
                    )
                )
            else:
                self.posts_list_view.controls.append(PostView(post=post))

        self.update()
        return True

    def load_posts_on_scroll(self, e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 100:
            if semaphore.acquire(blocking=False):
                try:
                    self.load_more_posts()
                finally:
                    semaphore.release()

    def enter_creds(self, e):
        def set_creds(e):
            self.username = str(username_field.value)
            self.client.set_auth(self.username, str(password_field.value))
            self.new_post_button.disabled = False
            self.user_info.value = f"Logged in as: {self.username}"
            self.refresh()
            self.page.close(dialog)

        username_field = ft.TextField(label="Username", autofocus=True)
        password_field = ft.TextField(label="Password", password=True)
        dialog = ft.AlertDialog(
            title=ft.Text("API Credentials"),
            content=ft.Column([username_field, password_field], tight=True),
            actions=[
                ft.ElevatedButton("Cancel", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Save", on_click=set_creds),
            ],
            modal=True,
        )
        self.page.open(dialog)

    def new_post(self, e):
        def submit_post(e):
            post = self.client.new_post(
                title=str(title_field.value), body=str(body_field.value)
            )
            self.posts_list_view.controls.insert(0, PostView(post))
            self.update()
            self.page.close(dialog)

        title_field = ft.TextField(label="Title", autofocus=True, max_length=100)
        body_field = ft.TextField(
            label="Body", multiline=True, min_lines=5, max_lines=10, max_length=5000
        )

        dialog = ft.AlertDialog(
            title=ft.Text("New Post"),
            content=ft.Column([title_field, body_field], tight=True, width=500),
            actions=[
                ft.ElevatedButton("Cancel", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Submit", on_click=submit_post),
            ],
        )
        self.page.open(dialog)

    def edit_post(self, postview: PostView):
        def submit_post(e):
            title = str(title_field.value)
            body = str(body_field.value)
            post = self.client.edit_post(
                post_id=postview.post.id, title=title, body=body
            )
            self.page.close(dialog)
            postview.post = post
            postview.update()

        title_field = ft.TextField(
            value=postview.post.title, label="Title", autofocus=True, max_length=100
        )
        body_field = ft.TextField(
            value=postview.post.body,
            label="Body",
            multiline=True,
            min_lines=5,
            max_lines=10,
            max_length=5000,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Post"),
            content=ft.Column([title_field, body_field], tight=True, width=500),
            actions=[
                ft.ElevatedButton("Cancel", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Submit", on_click=submit_post),
            ],
        )
        self.page.open(dialog)

    def delete_post(self, postview: PostView):
        def delete_post(e):
            self.client.delete_post(post_id=postview.post.id)
            self.page.close(dialog)
            self.posts_list_view.controls.remove(postview)
            self.posts_list_view.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Delete '{postview.post.title}'?"),
            actions=[
                ft.ElevatedButton("Cancel", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Delete", on_click=delete_post),
            ],
        )
        self.page.open(dialog)


def main(page: ft.Page):
    client = FlaskrClient()
    flaskr_app = FlaskrApp(client=client)
    page.add(flaskr_app)
    flaskr_app.refresh()


ft.app(target=main)
