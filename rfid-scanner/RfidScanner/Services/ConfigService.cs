using System.IO;
using System.Net.Http;
using Newtonsoft.Json;

namespace RfidScanner.Services;

/// <summary>
/// Настройки приложения
/// </summary>
public class AppSettings
{
    /// <summary>URL бэкенда PAPI (например, http://192.168.1.100:8080)</summary>
    public string BackendUrl { get; set; } = "http://localhost:8080";
    
    /// <summary>API-ключ RFID-сканера</summary>
    public string ApiKey { get; set; } = string.Empty;
    
    /// <summary>Режим сканера: HID (клавиатура) или TCP (сокет)</summary>
    public ScannerMode ScannerMode { get; set; } = ScannerMode.Hid;
    
    /// <summary>IP-адрес TCP-ридера (для режима TCP)</summary>
    public string TcpReaderIp { get; set; } = "192.168.1.100";
    
    /// <summary>Порт TCP-ридера (по умолчанию 8000)</summary>
    public int TcpReaderPort { get; set; } = 8000;
    
    /// <summary>Автоматическая синхронизация при подключении</summary>
    public bool AutoSyncOnConnect { get; set; } = true;
    
    /// <summary>Звуковой сигнал при успешном сканировании</summary>
    public bool EnableSound { get; set; } = true;
    
    /// <summary>Пауза между сканированиями (мс)</summary>
    public int ScanDebounceMs { get; set; } = 100;
    
    /// <summary>Сохранённая тема приложения</summary>
    public string Theme { get; set; } = "Light";
}

public enum ScannerMode
{
    Hid,      // Эмуляция клавиатуры (RFID)
    Nfc,      // Эмуляция клавиатуры (NFC)
    Tcp,      // TCP/IP сокет
    Serial    // RS232
}

/// <summary>
/// Сервис управления настройками
/// </summary>
public class ConfigService
{
    private readonly string _settingsPath;
    private AppSettings _settings = new();

    public AppSettings Settings => _settings;

    public ConfigService()
    {
        var appData = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "PAPI", "RfidScanner");
        Directory.CreateDirectory(appData);
        _settingsPath = Path.Combine(appData, "settings.json");
    }

    public void Load()
    {
        if (File.Exists(_settingsPath))
        {
            try
            {
                var json = File.ReadAllText(_settingsPath);
                _settings = JsonConvert.DeserializeObject<AppSettings>(json) ?? new();
            }
            catch
            {
                _settings = new();
            }
        }
    }

    public void Save()
    {
        var json = JsonConvert.SerializeObject(_settings, Formatting.Indented);
        File.WriteAllText(_settingsPath, json);
    }

    public void SetBackendUrl(string url)
    {
        _settings.BackendUrl = url.TrimEnd('/');
        Save();
    }

    public void SetApiKey(string key)
    {
        _settings.ApiKey = key;
        Save();
    }

    public void SetScannerMode(ScannerMode mode)
    {
        _settings.ScannerMode = mode;
        Save();
    }

    public void SetTheme(string theme)
    {
        _settings.Theme = theme;
        Save();
    }

    public string GetTheme()
    {
        return _settings.Theme ?? "Light";
    }

    /// <summary>
    /// Проверяет доступность сервера по URL из настроек
    /// </summary>
    public async Task<bool> CheckConnectivityAsync()
    {
        try
        {
            var baseUrl = _settings.BackendUrl.TrimEnd('/');
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(5);
            
            // Пытаемся достучаться до корня URL — это самый быстрый способ
            var response = await client.GetAsync(baseUrl);
            return response.IsSuccessStatusCode || response.StatusCode == System.Net.HttpStatusCode.NotFound;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Проверяет доступность сервера по произвольному URL
    /// </summary>
    public static async Task<bool> CheckConnectivityAsync(string url)
    {
        try
        {
            var baseUrl = url.TrimEnd('/');
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(5);
            
            var response = await client.GetAsync(baseUrl);
            return response.IsSuccessStatusCode || response.StatusCode == System.Net.HttpStatusCode.NotFound;
        }
        catch
        {
            return false;
        }
    }
}
