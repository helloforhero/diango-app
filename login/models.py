from django.db import models
# Create by Hfutbbs at 2019.11.2

# Create your models here.

class User(models.Model):
    gender = (
        ('male',"男"),
        ('female', "女"),
    )
    username = models.CharField(max_length=128, unique=True)
    passwd = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    sex = models.CharField(max_length=32, choices=gender, default="男")
    create_time = models.DateTimeField(auto_now_add=True)
    user_confirmed = models.BooleanField(default=False)


    def __str__(self):
        return self.username

    class Meta:
        ordering = ["-create_time"]
        verbose_name = "用户"
        verbose_name_plural = "用户"


class ConfirmUser(models.Model):
    confirm_code = models.CharField(max_length=256)
    user = models.OneToOneField('User', on_delete=models.CASCADE, db_constraint=False)
    create_time = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.user.username+ ": " +self.confirm_code


    class Meta:
        ordering = ["-create_time"]
        verbose_name = "确认码"
        verbose_name_plural = "确认码"

