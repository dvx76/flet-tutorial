from typing import Callable, Optional

import flet as ft

from flaskrclient import BlogPost, FlaskrClient


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
        self.new_post_button = ft.ElevatedButton(
            text="New Post", on_click=self.new_post, disabled=True
        )
        self.posts_list_view = ft.Column()
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text(
                        value="FlaskR Blog",
                        theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
                    ),
                    ft.IconButton(icon=ft.Icons.SETTINGS, on_click=self.enter_creds),
                ],
            ),
            self.new_post_button,
            self.posts_list_view,
        ]

    def refresh(self):
        postview_list = []
        for post in self.client.posts():
            if self.client.authenticated and self.username == post.author:
                postview_list.append(
                    PostView(
                        post=post, on_edit=self.edit_post, on_delete=self.delete_post
                    )
                )
            else:
                postview_list.append(PostView(post=post))
        self.posts_list_view.controls = postview_list
        self.update()

    def enter_creds(self, e):
        def set_creds(e):
            self.username = str(username_field.value)
            self.client.set_auth(self.username, str(password_field.value))
            self.new_post_button.disabled = False
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
