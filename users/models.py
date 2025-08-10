from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN_TCI_CAO = 'ADMIN_TCI_CAO', 'Admin Tối cao'
        ADMIN_DON_VI = 'ADMIN_DON_VI', 'Admin Đơn vị'
        LANH_DAO_CO_QUAN = 'LANH_DAO_CO_QUAN', 'Lãnh đạo Cơ quan'
        LANH_DAO_PHONG = 'LANH_DAO_PHONG', 'Lãnh đạo Phòng'
        CHUYEN_VIEN = 'CHUYEN_VIEN', 'Chuyên viên'
        CHUYEN_VIEN_VAN_PHONG = 'CHUYEN_VIEN_VAN_PHONG', 'Chuyên viên Văn phòng'

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CHUYEN_VIEN)
    co_quan = models.ForeignKey('core.CoQuan', on_delete=models.CASCADE, null=True, blank=True)
    phong_ban = models.ForeignKey('core.PhongBan', on_delete=models.CASCADE, null=True, blank=True)
    zalo_user_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Zalo User ID')