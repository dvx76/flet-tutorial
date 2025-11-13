from typing import Callable, Optional

import flet as ft

from flaskrclient import Client, Post


class PostView(ft.Column):
    def __init__(
        self, post: Post, on_edit: Optional[Callable], on_delete: Optional[Callable]
    ):
        super().__init__(spacing=0)
        self.post = post
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._build()

    def update_post(self, post: Post):
        self.post = post
        self._build()
        self.update()

    def _build(self):
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
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        self.post.title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM
                    ),
                    interaction_buttons,
                ],
            ),
            ft.Text(
                f"by {self.post.username} on {self.post.created}",
                theme_style=ft.TextThemeStyle.LABEL_SMALL,
            ),
            ft.Text(self.post.body),
            ft.Divider(),
        ]


class FlaskrApp(ft.Column):
    def __init__(self, client: Client):
        super().__init__(width=600)
        self.client = client
        self.posts = ft.Column()
        self.username: str = ""
        self.password: str = ""
        self.logged_as = ft.Text()
        self.new_post_button = ft.ElevatedButton(
            text="New Post", on_click=self.new_post, disabled=True
        )
        self.controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    self.logged_as,
                    ft.Text(
                        value="FlaskR Blog",
                        theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS, on_click=self.enter_creds
                            ),
                            ft.IconButton(icon=ft.Icons.REFRESH, on_click=self.refresh),
                        ]
                    ),
                ],
            ),
            self.new_post_button,
            self.posts,
        ]

    def refresh(self, e):
        if self.client.authenticated:
            on_edit = self.edit_post
            on_delete = self.delete_post
        else:
            on_edit, on_delete = None, None
        self.posts.controls = [
            PostView(post=post, on_edit=on_edit, on_delete=on_delete)
            for post in self.client.posts()
        ]
        self.update()

    def enter_creds(self, e):
        def set_creds(e):
            self.username = str(username_field.value)
            self.password = str(password_field.value)
            self.client.set_auth(self.username, self.password)
            self.new_post_button.disabled = False
            self.logged_as.value = f"Logged in as: {self.username}"
            self.page.close(dialog)
            self.refresh(None)

        username_field = ft.TextField(
            value=self.username, label="Username", autofocus=True
        )
        password_field = ft.TextField(
            value=self.password, label="Password", password=True
        )
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
            self.client.new_post(title=title_field.value, body=body_field.value)
            self.page.close(dialog)
            self.refresh(None)

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
            self.client.edit_post(
                post_id=postview.post.id, title=title_field.value, body=body_field.value
            )
            self.page.close(dialog)
            post.title = title_field.value
            post.body = body_field.value
            postview.update_post(post=post)

        post = postview.post
        title_field = ft.TextField(
            value=post.title, label="Title", autofocus=True, max_length=100
        )
        body_field = ft.TextField(
            value=post.body,
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
            self.posts.controls.remove(postview)
            self.posts.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Delete '{postview.post.title}'?"),
            actions=[
                ft.ElevatedButton("Cancel", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton("Delete", on_click=delete_post),
            ],
        )
        self.page.open(dialog)


def main(page: ft.Page):
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    flaskr_app = FlaskrApp(client=Client())
    page.add(flaskr_app)
    flaskr_app.refresh(None)


ft.app(target=main)
