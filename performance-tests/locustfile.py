from locust import between
from locust import HttpUser
from locust import task


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def load_test(self):
        self.client.get('/')
