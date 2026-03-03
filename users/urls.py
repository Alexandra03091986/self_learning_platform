from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.apps import UsersConfig
from users.views import CourseStudentsView, LoginView, UserDetailView, UserListView, UserRegisterView

app_name = UsersConfig.name


urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("courses/<int:course_id>/students/", CourseStudentsView.as_view(), name="course-students"),
]
