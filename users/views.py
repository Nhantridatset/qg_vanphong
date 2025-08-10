from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Import messages
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def user_list(request):
    if request.user.is_superuser:
        users = CustomUser.objects.all()
    elif request.user.is_authenticated and request.user.role == 'admin_co_quan' and request.user.co_quan:
        users = CustomUser.objects.filter(co_quan=request.user.co_quan)
    else:
        users = CustomUser.objects.none() # Other roles see no users by default
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def user_detail(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if request.user.is_authenticated and request.user.role == 'admin_co_quan':
        if user_obj.co_quan != request.user.co_quan:
            messages.error(request, 'Bạn không có quyền truy cập người dùng này.')
            return redirect('user_list')
    return render(request, 'users/user_detail.html', {'user': user_obj})

@login_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, user=request.user) # Pass user to form
        if form.is_valid():
            new_user = form.save(commit=False)
            if request.user.is_authenticated and request.user.role == 'admin_co_quan':
                new_user.co_quan = request.user.co_quan # Force co_quan for admin_co_quan
            new_user.save()
            messages.success(request, 'Người dùng đã được tạo thành công.')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm(user=request.user) # Pass user to form
    return render(request, 'users/user_form.html', {'form': form})

@login_required
def user_update(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if request.user.is_authenticated and request.user.role == 'admin_co_quan':
        if user_obj.co_quan != request.user.co_quan:
            messages.error(request, 'Bạn không có quyền cập nhật người dùng này.')
            return redirect('user_list')
        # Prevent admin_co_quan from changing their own role or co_quan
        if user_obj == request.user:
            messages.warning(request, 'Bạn không thể tự thay đổi vai trò hoặc cơ quan của mình.')
            # Note: Form fields will be disabled by CustomUserChangeForm logic

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_obj, user=request.user) # Pass user to form
        if form.is_valid():
            updated_user = form.save(commit=False)
            if request.user.is_authenticated and request.user.role == 'admin_co_quan':
                updated_user.co_quan = user_obj.co_quan # Keep original co_quan for admin_co_quan
            updated_user.save()
            messages.success(request, 'Người dùng đã được cập nhật thành công.')
            return redirect('user_detail', pk=pk)
    else:
        form = CustomUserChangeForm(instance=user_obj, user=request.user) # Pass user to form
    return render(request, 'users/user_form.html', {'form': form})

@login_required
def user_delete(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if request.user.is_authenticated and request.user.role == 'admin_co_quan':
        if user_obj.co_quan != request.user.co_quan:
            messages.error(request, 'Bạn không có quyền xóa người dùng này.')
            return redirect('user_list')
        if user_obj == request.user:
            messages.error(request, 'Bạn không thể tự xóa tài khoản của mình.')
            return redirect('user_detail', pk=pk) # Or user_list

    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'Người dùng đã được xóa thành công.')
        return redirect('user_list')
    return render(request, 'users/user_confirm_delete.html', {'user': user_obj})
