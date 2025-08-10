from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from core.models import CoQuan, PhongBan

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'role', 'co_quan', 'phong_ban', 'zalo_user_id')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None) # Get the request.user
        super().__init__(*args, **kwargs)

        # Default querysets
        self.fields['co_quan'].queryset = CoQuan.objects.all()
        self.fields['phong_ban'].queryset = PhongBan.objects.all()

        if self.request_user and self.request_user.is_authenticated and (self.request_user.role == 'admin_co_quan' or self.request_user.role == 'lanh_dao_co_quan'):
            if self.request_user.co_quan:
                self.fields['co_quan'].queryset = CoQuan.objects.filter(pk=self.request_user.co_quan.pk)
                self.fields['co_quan'].initial = self.request_user.co_quan
                self.fields['co_quan'].widget.attrs['readonly'] = True
                self.fields['phong_ban'].queryset = PhongBan.objects.filter(co_quan=self.request_user.co_quan)
            else:
                # If admin_co_quan/lanh_dao_co_quan has no co_quan assigned, they cannot create users
                for field_name in self.fields:
                    self.fields[field_name].widget.attrs['disabled'] = True

            # Restrict roles that admin_co_quan/lanh_dao_co_quan can create
            allowed_roles = [choice[0] for choice in CustomUser.ROLES if choice[0] not in ['admin', 'admin_co_quan', 'lanh_dao_co_quan']]
            self.fields['role'].choices = [(role, dict(CustomUser.ROLES)[role]) for role in allowed_roles]


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'co_quan', 'phong_ban', 'zalo_user_id')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None) # Get the request.user
        super().__init__(*args, **kwargs)

        # Default querysets
        self.fields['co_quan'].queryset = CoQuan.objects.all()
        self.fields['phong_ban'].queryset = PhongBan.objects.all()

        if self.request_user and self.request_user.is_authenticated and (self.request_user.role == 'admin_co_quan' or self.request_user.role == 'lanh_dao_co_quan'):
            if self.request_user.co_quan:
                self.fields['co_quan'].queryset = CoQuan.objects.filter(pk=self.request_user.co_quan.pk)
                self.fields['co_quan'].initial = self.request_user.co_quan
                self.fields['co_quan'].widget.attrs['readonly'] = True
                self.fields['phong_ban'].queryset = PhongBan.objects.filter(co_quan=self.request_user.co_quan)
            else:
                # If admin_co_quan/lanh_dao_co_quan has no co_quan assigned, they cannot edit users
                for field_name in self.fields:
                    self.fields[field_name].widget.attrs['disabled'] = True

            # Restrict roles that admin_co_quan/lanh_dao_co_quan can change to
            allowed_roles = [choice[0] for choice in CustomUser.ROLES if choice[0] not in ['admin', 'admin_co_quan', 'lanh_dao_co_quan']]
            self.fields['role'].choices = [(role, dict(CustomUser.ROLES)[role]) for role in allowed_roles]

            # Prevent admin_co_quan/lanh_dao_co_quan from changing their own role or co_quan
            if self.instance == self.request_user:
                self.fields['role'].widget.attrs['disabled'] = True
                self.fields['co_quan'].widget.attrs['disabled'] = True
                self.fields['phong_ban'].widget.attrs['disabled'] = True
