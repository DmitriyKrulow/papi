using System;
using System.IO;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Запись о попытке входа в систему
/// </summary>
public class LoginLogEntry
{
    public DateTime Timestamp { get; set; }
    public string Username { get; set; } = string.Empty;
    public bool Success { get; set; }
    public string Reason { get; set; } = string.Empty; // "OK", "Invalid username", "Invalid password", "Insufficient rights"
    public string? Role { get; set; }
}

/// <summary>
/// Сервис для ведения журнала попыток входа в систему
/// </summary>
public class LoginLogService
{
    private readonly string _logFilePath;
    private readonly object _lockObject = new object();

    public LoginLogService()
    {
        var logDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "PAPI", "RfidScanner", "logs");
        Directory.CreateDirectory(logDir);
        _logFilePath = Path.Combine(logDir, "login.log");
    }

    /// <summary>
    /// Записать попытку входа
    /// </summary>
    public void LogLoginAttempt(string username, bool success, string reason, string? role = null)
    {
        var entry = new LoginLogEntry
        {
            Timestamp = DateTime.Now,
            Username = username,
            Success = success,
            Reason = reason,
            Role = role
        };

        lock (_lockObject)
        {
            try
            {
                var jsonLine = JsonConvert.SerializeObject(entry) + Environment.NewLine;
                File.AppendAllText(_logFilePath, jsonLine);
            }
            catch
            {
                // Логирование не должно ронять приложение
            }
        }
    }

    /// <summary>
    /// Получить последние записи из лога
    /// </summary>
    public List<LoginLogEntry> GetLastEntries(int count = 50)
    {
        lock (_lockObject)
        {
            try
            {
                if (!File.Exists(_logFilePath))
                    return new List<LoginLogEntry>();

                var lines = File.ReadAllLines(_logFilePath);
                var lastLines = lines.Skip(Math.Max(0, lines.Length - count)).ToList();
                
                var entries = new List<LoginLogEntry>();
                foreach (var line in lastLines)
                {
                    try
                    {
                        entries.Add(JsonConvert.DeserializeObject<LoginLogEntry>(line)!);
                    }
                    catch
                    {
                        // Пропускаем невалидные строки
                    }
                }
                return entries;
            }
            catch
            {
                return new List<LoginLogEntry>();
            }
        }
    }

    /// <summary>
    /// Очистить лог
    /// </summary>
    public void ClearLog()
    {
        lock (_lockObject)
        {
            try
            {
                if (File.Exists(_logFilePath))
                    File.Delete(_logFilePath);
            }
            catch
            {
                // Игнорируем ошибки удаления
            }
        }
    }
}
