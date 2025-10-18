from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from stock.models import Warehouse

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('planner', 'Планировщик'),
    ('warehouse_head', 'Заведующий склад'),
    ('user', 'User'),
)


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='user'
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # auth.User bilan to‘qnashmaydi
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',
        # auth.User bilan to‘qnashmaydi
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username
    @property
    def full_name(self):
        return self.first_name + " " + self.last_name
