from django.contrib.auth.models import AbstractUser
from django.db import models
from .permissions import assign_user_role_group


class User(AbstractUser):
    ADMIN = "admin"
    GERENTE = "gerente"
    FUNCIONARIO = "funcionario"
    ROLE_CHOICES = [
        (ADMIN, "Administrador"),
        (GERENTE, "Gerente"),
        (FUNCIONARIO, "Funcionário"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=FUNCIONARIO)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_manager(self):
        return self.role in {self.ADMIN, self.GERENTE} or self.is_superuser

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_user_role_group(self)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    foto = models.ImageField(upload_to="usuarios", null=True, blank=True)
    tema = models.CharField(max_length=10, choices=[("dark", "Escuro"), ("light", "Claro")], default="dark") 
    telefone = models.CharField(max_length=30, blank=True)
    setor = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.user.username}"
