using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Сервис управления пользователями (локальное хранилище в JSON)
/// </summary>
public class UserService
{
    private readonly string _usersPath;
    private Dictionary<string, AppUser> _users = new();

    public UserService()
    {
        var dataDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "PAPI", "RfidScanner");
        Directory.CreateDirectory(dataDir);
        _usersPath = Path.Combine(dataDir, "users.json");
        Load();
    }

    /// <summary>
    /// Загрузить пользователей из файла
    /// </summary>
    private void Load()
    {
        if (File.Exists(_usersPath))
        {
            try
            {
                var json = File.ReadAllText(_usersPath);
                _users = JsonConvert.DeserializeObject<Dictionary<string, AppUser>>(json) ?? new();
            }
            catch
            {
                _users = new();
            }
        }

        // Гарантируем, что у всех пользователей есть PasswordHash
        foreach (var kvp in _users.ToList())
        {
            if (string.IsNullOrEmpty(kvp.Value.PasswordHash))
            {
                kvp.Value.PasswordHash = string.Empty;
            }
        }
    }

    /// <summary>
    /// Сохранить пользователей в файл
    /// </summary>
    private void Save()
    {
        var json = JsonConvert.SerializeObject(_users, Formatting.Indented);
        File.WriteAllText(_usersPath, json);
    }

    /// <summary>
    /// Проверить вход пользователя
    /// </summary>
    /// <param name="username">Имя пользователя</param>
    /// <param name="password">Пароль</param>
    /// <returns>AppUser если успешно, null если ошибка</returns>
    public AppUser? Authenticate(string username, string password)
    {
        if (string.IsNullOrWhiteSpace(username))
            return null;

        // Пустой пароль запрещён
        if (string.IsNullOrEmpty(password))
            return null;

        _users.TryGetValue(username.ToLower(), out var user);
        
        if (user == null)
            return null;

        // Пустой хеш пароля = учётка не настроена, доступ запрещён
        if (string.IsNullOrEmpty(user.PasswordHash))
            return null;

        // Проверка пароля (в реальном проекте — хеширование!)
        if (user.PasswordHash != password)
            return null;

        // Обновляем время последнего входа
        user.LastLogin = DateTime.Now;
        Save();

        return user;
    }

    /// <summary>
    /// Добавить нового пользователя
    /// </summary>
    public bool AddUser(string username, string password, UserRole role, string? department = null)
    {
        if (string.IsNullOrWhiteSpace(username))
            return false;

        if (_users.ContainsKey(username.ToLower()))
            return false;

        _users[username.ToLower()] = new AppUser
        {
            Username = username,
            Role = role,
            Department = department,
            PasswordHash = password,
            LastLogin = DateTime.Now
        };

        Save();
        return true;
    }

    /// <summary>
    /// Получить пользователя по имени
    /// </summary>
    public AppUser? GetUser(string username)
    {
        _users.TryGetValue(username.ToLower(), out var user);
        return user;
    }

    /// <summary>
    /// Получить всех пользователей
    /// </summary>
    public List<AppUser> GetAllUsers()
    {
        return new List<AppUser>(_users.Values);
    }

    /// <summary>
    /// Удалить пользователя
    /// </summary>
    public bool DeleteUser(string username)
    {
        return _users.Remove(username.ToLower());
    }

    /// <summary>
    /// Изменить пароль пользователя
    /// </summary>
    public bool ChangePassword(string username, string newPassword)
    {
        if (!_users.TryGetValue(username.ToLower(), out var user))
            return false;

        user.PasswordHash = newPassword;
        Save();
        return true;
    }
}
