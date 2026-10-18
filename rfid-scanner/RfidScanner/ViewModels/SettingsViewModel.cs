using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для страницы настроек
/// </summary>
public class SettingsViewModel : BaseViewModel
{
    private readonly ConfigService _config;

    private string _backendUrl;
    private string _apiKey;
    private ScannerMode _scannerMode;
    private string _tcpIp;
    private int _tcpPort;
    private bool _autoSync;
    private bool _enableSound;

    public SettingsViewModel(ConfigService config)
    {
        _config = config;
        _backendUrl = config.Settings.BackendUrl;
        _apiKey = config.Settings.ApiKey;
        _scannerMode = config.Settings.ScannerMode;
        _tcpIp = config.Settings.TcpReaderIp;
        _tcpPort = config.Settings.TcpReaderPort;
        _autoSync = config.Settings.AutoSyncOnConnect;
        _enableSound = config.Settings.EnableSound;
    }

    public string BackendUrl
    {
        get => _backendUrl;
        set => SetProperty(ref _backendUrl, value);
    }

    public string ApiKey
    {
        get => _apiKey;
        set => SetProperty(ref _apiKey, value);
    }

    public ScannerMode ScannerMode
    {
        get => _scannerMode;
        set => SetProperty(ref _scannerMode, value);
    }

    public string TcpIp
    {
        get => _tcpIp;
        set => SetProperty(ref _tcpIp, value);
    }

    public int TcpPort
    {
        get => _tcpPort;
        set => SetProperty(ref _tcpPort, value);
    }

    public bool AutoSync
    {
        get => _autoSync;
        set => SetProperty(ref _autoSync, value);
    }

    public bool EnableSound
    {
        get => _enableSound;
        set => SetProperty(ref _enableSound, value);
    }

    public ICommand SaveCommand => new RelayCommand(Save);
    public ICommand TestConnectionCommand => new RelayCommand(TestConnection);

    private void Save()
    {
        _config.SetBackendUrl(BackendUrl);
        _config.SetApiKey(ApiKey);
        _config.SetScannerMode(ScannerMode);
        
        // Сохраняем TCP-параметры
        var settings = _config.Settings;
        settings.TcpReaderIp = TcpIp;
        settings.TcpReaderPort = TcpPort;
        settings.AutoSyncOnConnect = AutoSync;
        settings.EnableSound = EnableSound;
        _config.Save();
    }

    private async Task TestConnection()
    {
        // Реализовать проверку подключения
    }
}
