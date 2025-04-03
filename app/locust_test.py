# from locust import HttpUser, task, between, SequentialTaskSet, constant_throughput
# from faker import Faker
# from bs4 import BeautifulSoup
# import random
#
#
#
# class LocustWeb(SequentialTaskSet):
#     fake = Faker("ru_RU")
#
#     def extract_csrf(self, response):
#         soup = BeautifulSoup(response.text, "html.parser")
#         csrf_input = soup.find("input", {"name": "csrf_token"})
#         return csrf_input["value"] if csrf_input else None
#
#
#     @task(1)
#     def register_user(self):
#         with self.client.get("/user/register", catch_response=True) as get_response:
#             csrf_token = self.extract_csrf(get_response)
#
#             if not csrf_token:
#                 get_response.failure("CSRF token not found")
#                 return
#
#             user_data = {
#                 "csrf_token": csrf_token,
#                 "first_name": self.fake.first_name(),
#                 "last_name": self.fake.last_name(),
#                 "username": f"{self.fake.user_name()}_{self.fake.random_number(4)}",
#                 "email": self.fake.unique.email(),
#                 "password": "Qwer_12345!",
#                 "confirm_password": "Qwer_12345!"
#             }
#
#         with self.client.post(
#                 "/user/register",
#                 data=user_data,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as post_response:
#             if post_response.status_code != 302:
#                 post_response.failure(f"Ошибка регистрации: {post_response.status_code}")
#
#
#     @task(2)
#     def login_and_access_profile(self):
#         with self.client.get("/user/login", catch_response=True) as get_response:
#             csrf_token = self.extract_csrf(get_response)
#
#             if not csrf_token:
#                 get_response.failure("CSRF token not found")
#                 return
#
#             login_data = {
#                 "csrf_token": csrf_token,
#                 "username": "ivan",
#                 "password": "qqq22463202",
#                 "remember": True
#             }
#
#         with self.client.post(
#                 "/user/login",
#                 data=login_data,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as post_response:
#             if post_response.status_code != 302:
#                 post_response.failure(f"Ошибка входа: {post_response.status_code}")
#                 return
#
#         with self.client.get("/profile", catch_response=True) as profile_response:
#             if profile_response.status_code != 200:
#                 profile_response.failure(f"Ошибка загрузки профиля: {profile_response.status_code}")
#
#
#     @task(3)
#     def admin_login_and_create_user(self):
#         with self.client.get("/user/login", catch_response=True) as get_response:
#             csrf_token = self.extract_csrf(get_response)
#
#             if not csrf_token:
#                 get_response.failure("CSRF token not found")
#                 return
#
#             login_data = {
#                 "csrf_token": csrf_token,
#                 "username": "admin",
#                 "password": "admin_password",
#                 "remember": True
#             }
#
#         with self.client.post(
#                 "/user/login",
#                 data=login_data,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as post_response:
#             if post_response.status_code != 302:
#                 post_response.failure(f"Ошибка входа: {post_response.status_code}")
#                 return
#
#         with self.client.get("/admin/users/create", catch_response=True) as create_user_get_response:
#             csrf_token = self.extract_csrf(create_user_get_response)
#
#             if not csrf_token:
#                 create_user_get_response.failure("CSRF token not found on create user page")
#                 return
#
#             new_username = self.fake.user_name()
#             new_email = self.fake.email()
#             new_password = "Qwer_12345!"
#             create_user_data = {
#                 "csrf_token": csrf_token,
#                 "username": new_username,
#                 "email": new_email,
#                 "first_name": self.fake.first_name(),
#                 "last_name": self.fake.last_name(),
#                 "password": new_password,
#                 "confirm_password": new_password,
#                 "role_id": 2
#             }
#
#         with self.client.post(
#                 "/admin/users/create",
#                 data=create_user_data,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as create_user_post_response:
#             if create_user_post_response.status_code != 302:
#                 create_user_post_response.failure(
#                     f"Ошибка создания пользователя: {create_user_post_response.status_code}")
#                 return
#
#
#     @task(4)
#     def admin_login_and_delete_user(self):
#         with self.client.get("/user/login", catch_response=True) as get_response:
#             csrf_token = self.extract_csrf(get_response)
#
#             if not csrf_token:
#                 get_response.failure("CSRF token not found")
#                 return
#
#             login_data = {
#                 "csrf_token": csrf_token,
#                 "username": "user",
#                 "password": "qqq22463202",
#                 "remember": True
#             }
#
#         with self.client.post(
#                 "/user/login",
#                 data=login_data,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as post_response:
#             if post_response.status_code != 302:
#                 post_response.failure(f"Ошибка входа: {post_response.status_code}")
#                 return
#
#         with self.client.get("/admin/users", catch_response=True) as users_get_response:
#             if users_get_response.status_code != 200:
#                 users_get_response.failure(f"Не удалось получить список пользователей: {users_get_response.status_code}")
#                 return
#
#             soup = BeautifulSoup(users_get_response.text, "html.parser")
#
#             table = soup.find("table", class_="table")
#             if not table:
#                 users_get_response.failure("Таблица пользователей не найдена")
#                 return
#
#             rows = table.find("tbody").find_all("tr")
#
#             random_row = random.choice(rows)
#
#             user_id_element = random_row.find("td")
#
#             user_id = user_id_element.text.strip()
#
#         delete_url = f"/admin/users/delete/{user_id}"
#         with self.client.post(
#                 delete_url,
#                 catch_response=True,
#                 allow_redirects=False
#         ) as delete_response:
#             if delete_response.status_code != 302:
#                 delete_response.failure(f"Ошибка удаления пользователя: {delete_response.status_code}")
#                 return
#
# class WebsiteUser(HttpUser):
#     wait_time = constant_throughput(3)
#     tasks = [
#         LocustWeb
#     ]