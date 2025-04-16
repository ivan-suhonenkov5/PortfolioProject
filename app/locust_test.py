from locust import HttpUser, task, between, SequentialTaskSet, constant_throughput
from faker import Faker
from bs4 import BeautifulSoup
import random


class LocustWeb(SequentialTaskSet):
    fake = Faker("ru_RU")

    def extract_csrf(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrf_token"})
        return csrf_input["value"] if csrf_input else None

    @task
    def register_user(self):
        with self.client.get("/user/register", catch_response=True) as get_response:
            csrf_token = self.extract_csrf(get_response)

            if not csrf_token:
                get_response.failure("CSRF токен не найден")
                return

            user_data = {
                "csrf_token": csrf_token,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "username": f"{self.fake.user_name()}_{self.fake.random_number(4)}",
                "email": self.fake.unique.email(),
                "password": "Qwer_12345!",
                "confirm_password": "Qwer_12345!"
            }

        with self.client.post(
                "/user/register",
                data=user_data,
                catch_response=True,
                allow_redirects=False
        ) as post_response:
            if post_response.status_code != 302:
                post_response.failure(f"Ошибка регистрации: {post_response.status_code}")

    @task
    def login_and_access_profile(self):
        with self.client.get("/user/login", catch_response=True) as get_response:
            csrf_token = self.extract_csrf(get_response)

            if not csrf_token:
                get_response.failure("CSRF не найден")
                return

            login_data = {
                "csrf_token": csrf_token,
                "username": "ivan12",
                "password": "qqq22463202",
                "remember": True
            }

        with self.client.post(
                "/user/login",
                data=login_data,
                catch_response=True,
                allow_redirects=False
        ) as post_response:
            if post_response.status_code != 302:
                post_response.failure(f"Ошибка входа: {post_response.status_code}")
                return

        with self.client.get("/profile", catch_response=True) as profile_response:
            if profile_response.status_code != 200:
                profile_response.failure(f"Ошибка загрузки профиля: {profile_response.status_code}")

    @task
    def admin_login_and_create_user(self):
        with self.client.get("/user/login", catch_response=True) as get_response:
            csrf_token = self.extract_csrf(get_response)

            if not csrf_token:
                get_response.failure("CSRF не найден")
                return

            login_data = {
                "csrf_token": csrf_token,
                "username": "admin",
                "password": "qqq22463202",
                "remember": True
            }

        with self.client.post(
                "/user/login",
                data=login_data,
                catch_response=True,
                allow_redirects=False
        ) as post_response:
            if post_response.status_code != 302:
                post_response.failure(f"Ошибка входа: {post_response.status_code}")
                return

        with self.client.get("/admin/users/create", catch_response=True) as create_user_get_response:
            csrf_token = self.extract_csrf(create_user_get_response)

            if not csrf_token:
                create_user_get_response.failure("CSRF токен не найден")
                return

            new_username = self.fake.user_name()
            new_email = self.fake.email()
            new_password = "Qwer_12345!"
            create_user_data = {
                "csrf_token": csrf_token,
                "username": new_username,
                "email": new_email,
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "password": new_password,
                "confirm_password": new_password,
                "role_id": 2
            }

        with self.client.post(
                "/admin/users/create",
                data=create_user_data,
                catch_response=True,
                allow_redirects=False
        ) as create_user_post_response:
            if create_user_post_response.status_code != 302:
                create_user_post_response.failure(
                    f"Ошибка создания пользователя: {create_user_post_response.status_code}")
                return

    @task
    def admin_login_and_delete_user(self):
        with self.client.get("/user/login", catch_response=True) as r:
            csrf = self.extract_csrf(r)
            self.client.post("/user/login", data={
                "csrf_token": csrf,
                "username": "admin",
                "password": "qqq22463202",
                "remember": True
            }, allow_redirects=False)

        with self.client.get("/admin/users", catch_response=True) as r:
            soup = BeautifulSoup(r.text, "html.parser")
            csrf = self.extract_csrf(r)
            user_id = max([
                int(form["action"].split("/")[-1])
                for form in soup.find_all("form", action=lambda x: "delete" in x)
                if form.get("action")
            ])

        self.client.post(
            f"/admin/users/delete/{user_id}",
            data={"csrf_token": csrf},
            allow_redirects=False
        )

    @task
    def login_and_delete_last_work(self):
        with self.client.get("/user/login", catch_response=True) as login_page:
            csrf = self.extract_csrf(login_page)

        login_data = {
            "csrf_token": csrf,
            "username": "ivan12",
            "password": "qqq22463202",
            "remember": True
        }

        with self.client.post(
            "/user/login",
            data=login_data,
            catch_response=True,
            allow_redirects=False
        ) as login_response:
            if login_response.status_code != 302:
                login_response.failure("Ошибка при логине ivan12")
                return

        with self.client.get("/profile", catch_response=True) as profile_response:
            if profile_response.status_code != 200:
                profile_response.failure("Не удалось загрузить профиль")
                return

            soup = BeautifulSoup(profile_response.text, "html.parser")

            delete_forms = soup.find_all("form", action=lambda x: x and "/work/delete/" in x)
            if not delete_forms:
                profile_response.failure("Нет доступных работ для удаления")
                return

            latest_form = max(delete_forms, key=lambda form: int(form["action"].split("/")[-1]))
            work_id = int(latest_form["action"].split("/")[-1])

            csrf_input = latest_form.find("input", {"name": "csrf_token"})
            csrf_token = csrf_input["value"] if csrf_input else None

            if not csrf_token:
                profile_response.failure("CSRF токен не найден в форме удаления")
                return

        with self.client.post(
            f"/work/delete/{work_id}",
            data={"csrf_token": csrf_token},
            catch_response=True,
            allow_redirects=False
        ) as delete_response:
            if delete_response.status_code != 302:
                delete_response.failure(f"Не удалось удалить работу {work_id}")



class WebsiteUser(HttpUser):
    wait_time = constant_throughput(3)
    tasks = [
        LocustWeb
    ]
