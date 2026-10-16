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

    private ObservableCollection<Room> _rooms = new();
    private ObservableCollection<Inventory> _inventories = new();
    private Room? _selectedRoom;
    private Inventory? _selectedInventory;
    private string _searchText = "";
    private bool _isLoading;
    private string _statusMessage = "Выберите помещение или инвентаризацию";
    private bool _showInventories;
    private ScanSession? _currentSession;
    private bool _isScanning;
    private bool _isInventoryInProgress;

    public RoomSelectorViewModel(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit)
    {
        _apiClient = apiClient;
        _sessionManager = sessionManager;
        _assetCache = assetCache;
        _audit = audit;
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
        set
        {
            if (SetProperty(ref _selectedInventory, value))
            {
                System.Diagnostics.Debug.WriteLine($"[RoomSelectorViewModel] SelectedInventory changed to: {value?.Name ?? "null"}");
            }
        }
    }

    // Метод для явного установки выбранной инвентаризации из code-behind
    public void SetSelectedInventory(Inventory inventory)
    {
        SelectedInventory = inventory;
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

    /// <summary>
    /// true — показывать список инвентаризаций (кнопка "Продолжить"),
    /// false — показывать помещения (кнопка "Начать инвентаризацию").
    /// Устанавливается ТОЛЬКО выбранной вкладкой через SetShowInventoriesList.
    /// </summary>
    public bool ShowInventories
    {
        get => _showInventories;
        private set => SetProperty(ref _showInventories, value);
    }

    public ScanSession? CurrentSession
    {
        get => _currentSession;
        private set => SetProperty(ref _currentSession, value);
    }

    public bool IsScanning
    {
        get => _isScanning;
        private set => SetProperty(ref _isScanning, value);
    }

    public ICommand LoadRoomsCommand => new RelayCommand(LoadRooms);
    public ICommand LoadInventoriesCommand => new RelayCommand(LoadInventories);
    public ICommand StartInventoryCommand => new RelayCommand(StartInventory);
    public ICommand ContinueInventoryCommand => new RelayCommand(ContinueInventory);

    public event Action? RoomsLoaded;
    
    /// <summary>
    /// Установить режим отображения (определяется выбранной вкладкой)
    /// </summary>
    public void SetShowInventoriesList(bool value)
    {
        if (SetProperty(ref _showInventories, value))
        {
            System.Diagnostics.Debug.WriteLine($"[SetShowInventoriesList] Now: {value}");
        }
    }
    
    /// <summary>
    /// Перезагрузка всех данных (вызывается при входе в режим выбора)
    /// НЕ меняет ShowInventories — это определяет выбранная вкладка
    /// </summary>
    public async void RefreshOnEnter()
    {
        System.Diagnostics.Debug.WriteLine("[RefreshOnEnter] START");
        try
        {
            await LoadInventoriesAsync();
            await LoadRoomsAsync();
            System.Diagnostics.Debug.WriteLine($"[RefreshOnEnter] DONE: Inventories={Inventories.Count}, Rooms={Rooms.Count}");
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[RefreshOnEnter] ERROR: {ex.GetType().Name}: {ex.Message}");
            System.Diagnostics.Debug.WriteLine($"[RefreshOnEnter] StackTrace: {ex.StackTrace}");
            StatusMessage = $"⚠ Не удалось обновить данные: {ex.Message}";
        }
    }

    /// <summary>
    /// Обновить только список инвентаризаций
    /// </summary>
    public async void RefreshInventories()
    {
        try
        {
            await LoadInventoriesAsync();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[RefreshInventories] ERROR: {ex.Message}");
            StatusMessage = $"⚠ Не удалось обновить список: {ex.Message}";
        }
    }

    private void LoadRooms() => _ = LoadRoomsAsync();
    private void LoadInventories() => _ = LoadInventoriesAsync();

    private async Task LoadRoomsAsync()
    {
        IsLoading = true;
        StatusMessage = "Загрузка помещений...";
        // ShowInventories НЕ трогаем — его задаёт выбранная вкладка

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

    private async Task LoadInventoriesAsync()
    {
        IsLoading = true;
        StatusMessage = "Загрузка инвентаризаций...";
        // ShowInventories НЕ трогаем — его задаёт выбранная вкладка

        try
        {
            var inventories = await _apiClient.GetActiveInventoriesAsync();
            Inventories.Clear();
            foreach (var inv in inventories)
                Inventories.Add(inv);
            
            StatusMessage = inventories.Count > 0 
                ? $"✅ Найдено {inventories.Count} активных инвентаризаций" 
                : "⚠ Нет активных инвентаризаций";
            
            System.Diagnostics.Debug.WriteLine($"[LoadInventoriesAsync] Loaded {inventories.Count} inventories");
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
        if (_isInventoryInProgress)
        {
            System.Diagnostics.Debug.WriteLine("[StartInventory] SKIPPED: Already in progress");
            return;
        }

        if (SelectedRoom == null)
        {
            StatusMessage = "⚠ Выберите помещение";
            return;
        }

        _isInventoryInProgress = true;
        IsLoading = true;
        StatusMessage = $"Создание инвентаризации для {SelectedRoom.Name}...";

        try
        {
            // Создаём инвентаризацию на сервере
            var result = await _apiClient.CreateInventoryAsync(SelectedRoom.Id, SelectedRoom.Name);
            
            int inventoryId = 0;
            if (result.ContainsKey("id"))
                inventoryId = Convert.ToInt32(result["id"]);

            if (inventoryId == 0)
            {
                StatusMessage = "⚠ Не удалось создать инвентаризацию на сервере";
                System.Diagnostics.Debug.WriteLine($"[StartInventory] ERROR: inventoryId=0, result keys: {string.Join(", ", result.Keys)}");
                return;
            }

            // Загружаем активы из созданной инвентаризации (те же, что сервер добавил)
            var inventoryItems = await _apiClient.GetInventoryAssetsAsync(inventoryId);
            
            System.Diagnostics.Debug.WriteLine($"[StartInventory] Got {inventoryItems.Count} items from server for room {SelectedRoom.Name}");

            // Конвертируем InventoryItem в Asset для кэша
            var assets = inventoryItems.Select(item => new Asset
            {
                RfidTag = item.RfidTag,
                Name = item.Name,
                InventoryNumber = item.InventoryNumber
            }).ToList();
            
            System.Diagnostics.Debug.WriteLine($"[StartInventory] Converted to {assets.Count} Assets");

            // Создаём локальную сессию с активами
            _sessionManager.CreateSession(SelectedRoom.Name, SelectedRoom.Id, inventoryId, assets);
            
            // Логируем начало
            _audit.Log(AuditAction.SessionStart, 
                roomName: SelectedRoom.Name,
                details: $"Инвентаризация создана: {SelectedRoom.Name} с {assets.Count} активами");
            
            StatusMessage = $"✅ Инвентаризация создана: {SelectedRoom.Name} ({assets.Count} активов)";
            
            // SessionManager.CreateSession уже вызвал SessionChanged → OnSessionCreated
            IsScanning = true;
        }
        catch (Exception ex)
        {
            StatusMessage = $"⚠ Ошибка: {ex.Message}";
            System.Diagnostics.Debug.WriteLine($"[StartInventory] ERROR: {ex.GetType().Name}: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
            _isInventoryInProgress = false;
        }
    }

    private async void ContinueInventory()
    {
        // Блокировка от повторных вызовов
        if (_isInventoryInProgress)
        {
            System.Diagnostics.Debug.WriteLine("[ContinueInventory] SKIPPED: Already in progress");
            return;
        }
        
        System.Diagnostics.Debug.WriteLine($"[ContinueInventory] SelectedInventory={SelectedInventory?.Name ?? "null"}, Id={SelectedInventory?.Id}");
        
        if (SelectedInventory == null)
        {
            StatusMessage = "⚠ Выберите инвентаризацию";
            System.Diagnostics.Debug.WriteLine("[ContinueInventory] ERROR: No inventory selected");
            return;
        }

        _isInventoryInProgress = true;
        IsLoading = true;
        StatusMessage = $"Загрузка активов для инвентаризации: {SelectedInventory.Name}...";
        System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Starting inventory: {SelectedInventory.Name}");

        try
        {
            // Загружаем активы инвентаризации
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Calling API: /api/rfid/inventories/{SelectedInventory.Id}/assets");
            var assets = await _apiClient.GetInventoryAssetsAsync(SelectedInventory.Id);
            
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Got {assets.Count} assets");
            
            // Используем scope_id из инвентаризации (надёжно)
            int roomId = SelectedInventory.ScopeId;
            
            // Fallback: если scope_id=0, пробуем распарсить из location первого актива
            if (roomId == 0 && assets.Count > 0 && !string.IsNullOrEmpty(assets[0].Location))
            {
                var parts = assets[0].Location.Split(new[] { " - " }, StringSplitOptions.None);
                if (parts.Length >= 2)
                {
                    int.TryParse(parts[1], out roomId);
                }
            }
            
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Using roomId={roomId}");
            
            // Конвертируем InventoryItem в Asset для кэша
            var assetList = assets.Select(item => new Asset
            {
                RfidTag = item.RfidTag,
                Name = item.Name,
                InventoryNumber = item.InventoryNumber
            }).ToList();
            
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Converted to {assetList.Count} Assets");
            
            // Создаём локальную сессию с активами
            _sessionManager.CreateSession(SelectedInventory.Name, roomId, SelectedInventory.Id, assetList);
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Session created: Id={_sessionManager.CurrentSession?.Id}, State={_sessionManager.CurrentSession?.State}");
            
            // Логируем продолжение
            _audit.Log(AuditAction.SessionStart, 
                roomName: SelectedInventory.Name,
                details: $"Продолжена инвентаризация: {SelectedInventory.Name} с {assets.Count} активами");
            
            StatusMessage = $"✅ Продолжена инвентаризация: {SelectedInventory.Name} ({assets.Count} активов)";
            
            // SessionManager.CreateSession уже вызвал SessionChanged → OnSessionCreated
            CurrentSession = _sessionManager.CurrentSession;
            IsScanning = true;
            
            // Сбрасываем выбранную инвентаризацию, чтобы избежать повторных вызовов
            SelectedInventory = null;
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[ContinueInventory] ERROR: {ex.GetType().Name}: {ex.Message}");
            if (ex.InnerException != null)
                System.Diagnostics.Debug.WriteLine($"[ContinueInventory] Inner: {ex.InnerException.Message}");
            StatusMessage = $"⚠ Ошибка: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
            _isInventoryInProgress = false;
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
