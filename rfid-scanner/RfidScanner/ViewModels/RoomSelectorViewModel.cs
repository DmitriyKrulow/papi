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
    private Room? _selectedRoom;
    private string _searchText = "";
    private bool _isLoading;
    private string _statusMessage = "Выберите помещение для инвентаризации";

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

    public Room? SelectedRoom
    {
        get => _selectedRoom;
        set => SetProperty(ref _selectedRoom, value);
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

    public ICommand LoadRoomsCommand => new RelayCommand(LoadRooms);
    public ICommand StartInventoryCommand => new RelayCommand(StartInventory);

    private async void LoadRooms()
    {
        IsLoading = true;
        StatusMessage = "Загрузка помещений...";

        try
        {
            // Загрузка списка помещений из API
            var rooms = await _apiClient.GetRoomsAsync();
            Rooms.Clear();
            foreach (var room in rooms)
                Rooms.Add(room);
            
            StatusMessage = rooms.Count > 0 
                ? $"✅ Загружено {rooms.Count} помещений" 
                : "⚠ Помещения не найдены";
        }
        catch
        {
            StatusMessage = "⚠ Сервер недоступен — проверьте подключение";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private void FilterRooms()
    {
        if (string.IsNullOrWhiteSpace(SearchText))
        {
            // Показываем все
            return;
        }

        // Фильтрация через CollectionView
        var view = System.Windows.Data.CollectionViewSource.GetDefaultView(Rooms);
        view.Filter = item =>
        {
            if (item is Room room)
                return room.Name?.ToLower().Contains(SearchText.ToLower()) == true ||
                       room.Building?.ToLower().Contains(SearchText.ToLower()) == true;
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
        StatusMessage = $"Загрузка активов для {SelectedRoom.Name}...";

        try
        {
            // Загружаем кэш активов для помещения
            var assets = await _apiClient.GetRoomAssetsAsync(SelectedRoom.Id);
            await _assetCache.LoadRoomAssetsAsync(SelectedRoom.Id, assets);
            
            // Создаём сессию
            _sessionManager.CreateSession(SelectedRoom.Name, SelectedRoom.Id);
            
            // Логируем начало
            _audit.Log(AuditAction.SessionStart, 
                roomName: SelectedRoom.Name,
                details: $"Начата инвентаризация помещения: {SelectedRoom.Name} " +
                        $"({assets.Count} активов)");
            
            StatusMessage = $"✅ Начата инвентаризация: {SelectedRoom.Name}";
        }
        catch
        {
            StatusMessage = "⚠ Ошибка загрузки — повторите попытку";
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
