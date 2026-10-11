using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для экрана выбора помещения
/// </summary>
public class RoomSelectorViewModel : INotifyPropertyChanged
{
    private readonly RfidApiClient _apiClient;
    private readonly SessionManager _sessionManager;
    private readonly AssetCacheService _assetCache;
    private readonly AuditService _audit;
    private readonly Action<ScanSession> _onInventoryStarted;

    private ObservableCollection<Room> _rooms = new();
    private ObservableCollection<Inventory> _inventories = new();
    private Room? _selectedRoom;
    private Inventory? _selectedInventory;
    private string _searchText = "";
    private bool _isLoading;
    private string _statusMessage = "Выберите помещение или инвентаризацию";
    private bool _showInventories;

    public RoomSelectorViewModel(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit, Action<ScanSession> onInventoryStarted)
    {
        _apiClient = apiClient;
        _sessionManager = sessionManager;
        _assetCache = assetCache;
        _audit = audit;
        _onInventoryStarted = onInventoryStarted;
    }

    public ObservableCollection<Room> Rooms
    {
        get => _rooms;
        private set => SetProperty(ref _rooms, value);
    }

    public ObservableCollection<Inventory> Inventories
    {
        get => _inventories;
        private set => SetProperty(ref _inventories, value);
    }

    public Room? SelectedRoom
    {
        get => _selectedRoom;
        set => SetProperty(ref _selectedRoom, value);
    }

    public Inventory? SelectedInventory
    {
        get => _selectedInventory;
        set => SetProperty(ref _selectedInventory, value);
    }

    public string SearchText
    {
        get => _searchText;
        set
        {
            if (SetProperty(ref _searchText, value))
                FilterRooms();
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        private set => SetProperty(ref _isLoading, value);
    }

    public string StatusMessage
    {
        get => _statusMessage;
        private set => SetProperty(ref _statusMessage, value);
    }

    public bool ShowInventories
    {
        get => _showInventories;
        set => SetProperty(ref _showInventories, value);
    }

    public ICommand LoadRoomsCommand => new RelayCommand(LoadRooms);
    public ICommand LoadInventoriesCommand => new RelayCommand(LoadInventories);
    public ICommand StartInventoryCommand => new RelayCommand(StartInventory);
    public ICommand ContinueInventoryCommand => new RelayCommand(ContinueInventory);

    public event Action? RoomsLoaded;

    private async void LoadRooms()
    {
        IsLoading = true;
        StatusMessage = "Загрузка помещений...";
        ShowInventories = false;

        try
        {
            var rooms = await _apiClient.GetRoomsAsync();
            Rooms.Clear();
            foreach (var room in rooms)
                Rooms.Add(room);
            
            StatusMessage = rooms.Count > 0 
                ? $"✅ Загружено {rooms.Count} помещений" 
                : "⚠ Помещения не найдены";
            
            RoomsLoaded?.Invoke();
        }
        catch (Exception ex)
        {
            StatusMessage = $"⚠ Ошибка: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async void LoadInventories()
    {
        IsLoading = true;
        StatusMessage = "Загрузка инвентаризаций...";
        ShowInventories = true;

        try
        {
            var inventories = await _apiClient.GetActiveInventoriesAsync();
            Inventories.Clear();
            foreach (var inv in inventories)
                Inventories.Add(inv);
            
            StatusMessage = inventories.Count > 0 
                ? $"✅ Найдено {inventories.Count} активных инвентаризаций" 
                : "⚠ Нет активных инвентаризаций";
        }
        catch (Exception ex)
        {
            StatusMessage = $"⚠ Ошибка загрузки: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private void FilterRooms()
    {
        var view = System.Windows.Data.CollectionViewSource.GetDefaultView(Rooms);
        
        if (string.IsNullOrWhiteSpace(SearchText))
        {
            view.Filter = null;
            return;
        }

        string query = SearchText.ToLower();
        view.Filter = item =>
        {
            if (item is Room room)
                return room.Name?.ToLower().Contains(query) == true ||
                       room.Building?.ToLower().Contains(query) == true ||
                       room.Floor?.ToLower().Contains(query) == true;
            return false;
        };
    }

    private async void StartInventory()
    {
        if (SelectedRoom == null)
        {
            StatusMessage = "⚠ Выберите помещение";
            return;
        }

        IsLoading = true;
        StatusMessage = $"Создание инвентаризации для {SelectedRoom.Name}...";

        try
        {
            // Создаём инвентаризацию на сервере
            var result = await _apiClient.CreateInventoryAsync(SelectedRoom.Id, SelectedRoom.Name);
            
            int inventoryId = 0;
            if (result.ContainsKey("id"))
                inventoryId = Convert.ToInt32(result["id"]);

            // Создаём локальную сессию
            _sessionManager.CreateSession(SelectedRoom.Name, SelectedRoom.Id, inventoryId);
            
            // Логируем начало
            _audit.Log(AuditAction.SessionStart, 
                roomName: SelectedRoom.Name,
                details: $"Инвентаризация создана: {SelectedRoom.Name}");
            
            StatusMessage = $"✅ Инвентаризация создана: {SelectedRoom.Name}";
            
            // Переключаемся на сканирование
            if (_sessionManager.CurrentSession != null)
                _onInventoryStarted(_sessionManager.CurrentSession);
        }
        catch (Exception ex)
        {
            StatusMessage = $"⚠ Ошибка: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async void ContinueInventory()
    {
        if (SelectedInventory == null)
        {
            StatusMessage = "⚠ Выберите инвентаризацию";
            return;
        }

        IsLoading = true;
        StatusMessage = $"Загрузка активов для инвентаризации: {SelectedInventory.Name}...";

        try
        {
            // Загружаем активы инвентаризации
            var assets = await _apiClient.GetInventoryAssetsAsync(SelectedInventory.Id);
            
            // Создаём локальную сессию
            _sessionManager.CreateSession(SelectedInventory.Name, 0, SelectedInventory.Id);
            
            // Логируем продолжение
            _audit.Log(AuditAction.SessionStart, 
                roomName: SelectedInventory.Name,
                details: $"Продолжена инвентаризация: {SelectedInventory.Name} с {assets.Count} активами");
            
            StatusMessage = $"✅ Продолжена инвентаризация: {SelectedInventory.Name} ({assets.Count} активов)";
            
            // Переключаемся на сканирование
            if (_sessionManager.CurrentSession != null)
                _onInventoryStarted(_sessionManager.CurrentSession);
        }
        catch (Exception ex)
        {
            StatusMessage = $"⚠ Ошибка: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(name);
        return true;
    }
}
