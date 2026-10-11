using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// Базовый ViewModel с поддержкой INotifyPropertyChanged
/// </summary>
public abstract class BaseViewModel : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (Equals(field, value))
            return false;
        field = value;
        OnPropertyChanged(name);
        return true;
    }
}

/// <summary>
/// Главный ViewModel
/// </summary>
public class MainViewModel : BaseViewModel
{
    private readonly ConfigService _config;
    private readonly RfidApiClient _apiClient;
    private readonly OfflineQueueService _offlineQueue;

    private string _statusMessage = "Инициализация...";
    private bool _isConnected;
    private int _pendingOfflineCount;
    private ObservableCollection<Inventory> _inventories = new();
    private Inventory? _selectedInventory;
    private bool _isLoading;

    public MainViewModel(ConfigService config)
    {
        _config = config;
        _apiClient = new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey);
        _offlineQueue = new OfflineQueueService();

        StatusMessage = config.Settings.ApiKey.Length > 0 
            ? "Готов к работе" 
            : "Настройте API-ключ в настройках";
    }

    public string StatusMessage
    {
        get => _statusMessage;
        set => SetProperty(ref _statusMessage, value);
    }

    public bool IsConnected
    {
        get => _isConnected;
        set => SetProperty(ref _isConnected, value);
    }

    public int PendingOfflineCount
    {
        get => _pendingOfflineCount;
        set => SetProperty(ref _pendingOfflineCount, value);
    }

    public ObservableCollection<Inventory> Inventories => _inventories;

    public Inventory? SelectedInventory
    {
        get => _selectedInventory;
        set => SetProperty(ref _selectedInventory, value);
    }

    public bool IsLoading
    {
        get => _isLoading;
        set => SetProperty(ref _isLoading, value);
    }

    public ICommand RefreshInventoriesCommand => new RelayCommand(RefreshInventories);
    public ICommand SyncOfflineCommand => new RelayCommand(SyncOffline);
    public ICommand OpenSettingsCommand => new RelayCommand(OpenSettings);

    private async void RefreshInventories()
    {
        IsLoading = true;
        StatusMessage = "Загрузка инвентаризаций...";

        try
        {
            var inventories = await _apiClient.GetActiveInventoriesAsync();
            _inventories.Clear();
            foreach (var inv in inventories)
                _inventories.Add(inv);

            StatusMessage = inventories.Count > 0 
                ? $"Загружено {inventories.Count} инвентаризаций" 
                : "Нет активных инвентаризаций";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Ошибка: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async void SyncOffline()
    {
        StatusMessage = "Синхронизация офлайн-операций...";
        var count = await _offlineQueue.SyncItemsAsync(async items =>
        {
            // Реализовать синхронизацию с бэкендом
            return true;
        });
        PendingOfflineCount = _offlineQueue.GetPendingCount();
        StatusMessage = count > 0 ? $"Синхронизировано {count} операций" : "Нет операций для синхронизации";
    }

    private void OpenSettings()
    {
        // Переход на страницу настроек
    }
}
