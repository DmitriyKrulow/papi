using System.ComponentModel;
using System.Runtime.CompilerServices;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

public class LoginViewModel : INotifyPropertyChanged
{
    private readonly UserService _userService;
    private readonly RoleService _roleService;
    private readonly LoginLogService _loginLogService;
    private readonly RfidApiClient _apiClient;

    private string _username = string.Empty;
    private string _password = string.Empty;
    private string _errorMessage = string.Empty;
    private bool _isLoading;
    private AppUser? _authenticatedUser;

    public string Username
    {
        get => _username;
        set
        {
            if (_username != value)
            {
                _username = value;
                OnPropertyChanged();
            }
        }
    }

    public string Password
    {
        get => _password;
        set
        {
            if (_password != value)
            {
                _password = value;
                OnPropertyChanged();
            }
        }
    }

    public string ErrorMessage
    {
        get => _errorMessage;
        private set
        {
            if (_errorMessage != value)
            {
                _errorMessage = value;
                OnPropertyChanged();
            }
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        private set
        {
            if (_isLoading != value)
            {
                _isLoading = value;
                OnPropertyChanged();
            }
        }
    }

    public AppUser? AuthenticatedUser => _authenticatedUser;

    public LoginViewModel(UserService userService, RoleService roleService, LoginLogService loginLogService, RfidApiClient apiClient)
    {
        _userService = userService;
        _roleService = roleService;
        _loginLogService = loginLogService;
        _apiClient = apiClient;
    }

    public async Task LoginAsync(string username, string password)
    {
        if (string.IsNullOrWhiteSpace(username))
        {
            ErrorMessage = "Введите имя пользователя";
            _loginLogService?.LogLoginAttempt(username, false, "Empty username");
            return;
        }

        if (string.IsNullOrEmpty(password))
        {
            ErrorMessage = "Введите пароль";
            _loginLogService?.LogLoginAttempt(username, false, "Empty password");
            return;
        }

        IsLoading = true;
        ErrorMessage = string.Empty;

        try
        {
            // Аутентификация через бэкенд:
            // 1. POST /api/auth/login  ->  {"access_token": "..."}
            // 2. GET  /api/auth/me     ->  {"id": 1, "username": "...", "role": "admin", ...}
            var result = await _apiClient.LoginAsync(username, password);
            
            if (result == null)
            {
                ErrorMessage = "Неверное имя пользователя или пароль";
                _loginLogService?.LogLoginAttempt(username, false, "Invalid credentials");
                return;
            }

            // result — это плоский объект UserResponse из /api/auth/me
            // Ключи: id, username, email, full_name, phone, role, department, is_active, created_at, updated_at

            // Определяем и маппим роль (бэкенд: "admin"/"user"/"responsible")
            var roleString = result.ContainsKey("role") ? result["role"]?.ToString()?.ToLowerInvariant() : null;
            UserRole? role = roleString switch
            {
                "admin" or "administrator" => UserRole.Administrator,
                "manager"                 => UserRole.Manager,
                "accountant"              => UserRole.Accountant,
                "responsible" or "inventory_checker" or "user" => UserRole.InventoryChecker,
                _ => null
            };

            if (role == null)
            {
                ErrorMessage = $"Неизвестная роль пользователя: {roleString ?? "(пусто)"}";
                _loginLogService?.LogLoginAttempt(username, false, $"Unknown role: {roleString}");
                return;
            }

            // Получаем имя отдела (может быть null — поле optional в UserResponse)
            var department = result.ContainsKey("department") ? result["department"]?.ToString() : null;

            // Авторизуем в RoleService
            _roleService.Login(username, role.Value, department);
            
            // Создаём локальную запись о пользователе
            _authenticatedUser = new AppUser
            {
                Username = username,
                Role = role.Value,
                Department = department,
                LastLogin = DateTime.Now
            };

            // Логируем успешный вход
            _loginLogService?.LogLoginAttempt(username, true, "OK", role.Value.ToString());
        }
        catch (Exception ex)
        {
            ErrorMessage = $"Ошибка соединения с сервером: {ex.Message}";
            _loginLogService?.LogLoginAttempt(username, false, $"Exception: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    public void Cancel()
    {
        // Просто закрываем окно
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
