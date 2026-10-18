using System;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Сервис управления ролями пользователей
/// </summary>
public class RoleService
{
    private AppUser? _currentUser;

    public AppUser? CurrentUser => _currentUser;

    /// <summary>
    /// Авторизация пользователя
    /// </summary>
    public void Login(string username, UserRole role, string? department = null)
    {
        _currentUser = new AppUser
        {
            Username = username,
            Role = role,
            Department = department,
            LastLogin = DateTime.Now
        };
    }

    /// <summary>
    /// Выход пользователя
    /// </summary>
    public void Logout()
    {
        _currentUser = null;
    }

    /// <summary>
    /// Проверка права: может ли пользователь экспортировать отчёты
    /// </summary>
    public bool CanExportReports()
    {
        return _currentUser?.Role is UserRole.Administrator or UserRole.Accountant or UserRole.Manager;
    }

    /// <summary>
    /// Проверка права: может ли пользователь управлять помещениями
    /// </summary>
    public bool CanManageRooms()
    {
        return _currentUser?.Role is UserRole.Administrator or UserRole.Manager;
    }

    /// <summary>
    /// Проверка права: может ли пользователь редактировать настройки
    /// </summary>
    public bool CanEditSettings()
    {
        return _currentUser?.Role == UserRole.Administrator;
    }

    /// <summary>
    /// Проверка права: может ли пользователь видеть все помещения (не только свои)
    /// </summary>
    public bool CanViewAllRooms()
    {
        return _currentUser?.Role is UserRole.Administrator or UserRole.Manager;
    }

    /// <summary>
    /// Проверка права: может ли пользователь удалять записи
    /// </summary>
    public bool CanDeleteRecords()
    {
        return _currentUser?.Role == UserRole.Administrator;
    }

    /// <summary>
    /// Проверка права: может ли пользователь проверять имущество
    /// (Ответственный или Администратор)
    /// </summary>
    public bool CanVerifyAssets()
    {
        return _currentUser?.Role is UserRole.Administrator or UserRole.Manager;
    }

    /// <summary>
    /// Получить текст роли для отображения
    /// </summary>
    public static string GetRoleText(UserRole role)
    {
        return role switch
        {
            UserRole.InventoryChecker => "Инвентаризатор",
            UserRole.Administrator => "Администратор",
            UserRole.Accountant => "Бухгалтер",
            UserRole.Manager => "Менеджер",
            _ => "Неизвестно"
        };
    }

    /// <summary>
    /// Получить список всех ролей
    /// </summary>
    public static UserRole[] GetAllRoles() => 
        (UserRole[])Enum.GetValues(typeof(UserRole));
}
