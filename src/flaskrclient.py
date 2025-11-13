from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class Post:
    id: int
    username: str
    created: datetime
    title: str
    body: str

    def __post_init__(self):
        if isinstance(self.created, str):
            self.created = datetime.fromisoformat(self.created)


class Client:
    url = "http://127.0.0.1:5000"

    def __init__(self):
        self.session = requests.Session()
        self.authenticated = False

    def set_auth(self, username: str, password: str):
        self.session.auth = (username, password)
        self.authenticated = True

    def posts(self) -> list[Post]:
        print("Gettings posts")
        response = self.session.get(f"{self.url}/posts")
        response.raise_for_status()
        data = response.json()
        print(f"Got {len(data)} posts")
        return [Post(**post_data) for post_data in data]

    def new_post(self, title: str, body: str):
        response = self.session.post(
            f"{self.url}/posts", json={"title": title, "body": body}
        )
        response.raise_for_status()

    def edit_post(self, post_id: int, title: str, body: str):
        response = self.session.put(
            f"{self.url}/posts/{post_id}", json={"title": title, "body": body}
        )
        response.raise_for_status()

    def delete_post(self, post_id: int):
        response = self.session.delete(f"{self.url}/posts/{post_id}")
        response.raise_for_status()
