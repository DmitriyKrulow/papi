using System;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for RoomSelectorView.xaml
/// </summary>
public partial class RoomSelectorView : UserControl
{
    private RoomSelectorViewModel? _viewModel;
    private SessionManager? _sessionManager;
    private Button? _roomsTabBtn;
    private Button? _inventoriesTabBtn;

    /// <summary>
    /// ViewModel для подписки на события из MainWindow
    /// </summary>
    public RoomSelectorViewModel? ViewModel => _viewModel;

    public RoomSelectorView()
    {
        InitializeComponent();
        
        _roomsTabBtn = RoomsTabBtn;
        _inventoriesTabBtn = InventoriesTabBtn;
    }

    public void Initialize(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit)
    {
        _sessionManager = sessionManager;
        
        _viewModel = new RoomSelectorViewModel(apiClient, sessionManager, assetCache, audit);
        DataContext = _viewModel;
        
        // Подписываемся на изменение ShowInventories
        _viewModel.PropertyChanged += (s, e) =>
        {
            if (e.PropertyName == nameof(RoomSelectorViewModel.ShowInventories))
            {
                Dispatcher.Invoke(() => UpdateListVisibility());
            }
        };
        
        // Вкладка "Помещения" выбрана по умолчанию → кнопка "Начать инвентаризацию"
        _viewModel.SetShowInventoriesList(false);
        
        // Автоматическая загрузка помещений и инвентаризаций
        _viewModel.LoadRoomsCommand.Execute(null);
        _viewModel.LoadInventoriesCommand.Execute(null);
        
        // Устанавливаем начальную видимость
        UpdateListVisibility();
    }

    private void StartButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        System.Diagnostics.Debug.WriteLine($"[StartButton_Click] ShowInventories={_viewModel.ShowInventories}");
        System.Diagnostics.Debug.WriteLine($"[StartButton_Click] SelectedRoom={_viewModel.SelectedRoom?.Name ?? "null"}");
        System.Diagnostics.Debug.WriteLine($"[StartButton_Click] SelectedInventory={_viewModel.SelectedInventory?.Name ?? "null"}");
        
        // Если вкладка инвентаризаций — используем SelectedInventory
        if (_viewModel.ShowInventories)
        {
            if (_viewModel.SelectedInventory == null)
            {
                System.Diagnostics.Debug.WriteLine("[StartButton_Click] ERROR: No inventory selected");
                _viewModel.StatusMessage = "⚠ Выберите инвентаризацию";
                return;
            }
            System.Diagnostics.Debug.WriteLine("[StartButton_Click] Executing ContinueInventory");
            _viewModel.ContinueInventoryCommand.Execute(null);
            return;
        }
        
        // Если вкладка помещений — ищем комнату
        var btn = sender as Button;
        var room = btn?.Tag as Room;
        
        // Если кнопка "Начать инвентаризацию" (без Tag) и есть SelectedRoom, используем его
        if (room == null && _viewModel.SelectedRoom != null)
        {
            room = _viewModel.SelectedRoom;
            System.Diagnostics.Debug.WriteLine($"[StartButton_Click] Using SelectedRoom from ViewModel: {room.Name}");
        }
        
        if (room == null)
        {
            System.Diagnostics.Debug.WriteLine("[StartButton_Click] ERROR: No room selected");
            _viewModel.StatusMessage = "⚠ Выберите помещение";
            return;
        }
        
        // Выделяем комнату
        SelectRoom(room);
        System.Diagnostics.Debug.WriteLine("[StartButton_Click] Executing StartInventory");
        _viewModel.StartInventoryCommand.Execute(null);
    }
    
    /// <summary>
    /// Выделить комнату (снять выделение с остальных)
    /// </summary>
    private void SelectRoom(Room room)
    {
        foreach (var r in _viewModel?.Rooms ?? Enumerable.Empty<Room>())
            r.ClearSelection();
        room.Selected = true;
    }
    
    /// <summary>
    /// Клик по вкладке "Помещения"
    /// </summary>
    public void RoomsTab_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        System.Diagnostics.Debug.WriteLine("[RoomsTab_Click] Switching to rooms");
        _viewModel.SetShowInventoriesList(false);
        _viewModel.LoadRoomsCommand.Execute(null);
        UpdateTabStyles("rooms");
        UpdateListVisibility();
    }
    
    /// <summary>
    /// Клик по вкладке "Инвентаризации"
    /// </summary>
    public void InventoriesTab_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        System.Diagnostics.Debug.WriteLine("[InventoriesTab_Click] BEFORE: ShowInventories=" + _viewModel.ShowInventories);
        _viewModel.SetShowInventoriesList(true);
        System.Diagnostics.Debug.WriteLine("[InventoriesTab_Click] AFTER: ShowInventories=" + _viewModel.ShowInventories);
        _viewModel.LoadInventoriesCommand.Execute(null);
        UpdateTabStyles("inventories");
        UpdateListVisibility();
    }
    
    /// <summary>
    /// Обновляет видимость списков на основе ShowInventories
    /// </summary>
    private void UpdateListVisibility()
    {
        if (RoomsListView == null || InventoriesListView == null) return;
        
        bool showInventories = _viewModel?.ShowInventories ?? false;
        
        RoomsListView.Visibility = showInventories ? Visibility.Collapsed : Visibility.Visible;
        InventoriesListView.Visibility = showInventories ? Visibility.Visible : Visibility.Collapsed;
        
        System.Diagnostics.Debug.WriteLine($"[UpdateListVisibility] ShowInventories={showInventories}, Rooms={RoomsListView.Visibility}, Inventories={InventoriesListView.Visibility}");
    }
    
    /// <summary>
    /// Обновляет стили кнопок вкладок
    /// </summary>
    private void UpdateTabStyles(string activeTab)
    {
        if (_roomsTabBtn == null || _inventoriesTabBtn == null) return;
        
        var activeBg = (Brush)FindResource("ThemeWidgetInfoBg");
        var activeFg = (Brush)FindResource("ThemeAccent");
        var activeWeight = FontWeights.SemiBold;
        var inactiveBg = Brushes.Transparent;
        var inactiveFg = (Brush)FindResource("ThemeTextSecondary");
        
        if (activeTab == "rooms")
        {
            _roomsTabBtn.Background = activeBg;
            _roomsTabBtn.Foreground = activeFg;
            _roomsTabBtn.FontWeight = activeWeight;
            
            _inventoriesTabBtn.Background = inactiveBg;
            _inventoriesTabBtn.Foreground = inactiveFg;
            _inventoriesTabBtn.FontWeight = FontWeights.Normal;
        }
        else
        {
            _inventoriesTabBtn.Background = activeBg;
            _inventoriesTabBtn.Foreground = activeFg;
            _inventoriesTabBtn.FontWeight = activeWeight;
            
            _roomsTabBtn.Background = inactiveBg;
            _roomsTabBtn.Foreground = inactiveFg;
            _roomsTabBtn.FontWeight = FontWeights.Normal;
        }
    }
    
    /// <summary>
    /// Обработчик клика по помещению для его выбора
    /// </summary>
    private void RoomCard_Click(object sender, MouseButtonEventArgs e)
    {
        if (_viewModel == null) return;
        
        // Находим комнату, которая принадлежит нажатой карточке
        var border = sender as Border;
        if (border?.DataContext is Room room)
        {
            SelectRoom(room);
            _viewModel.SelectedRoom = room;
        }
    }
    
    /// <summary>
    /// Обработчик клика по карточке инвентаризации для её выбора
    /// </summary>
    private void InventoryCard_Click(object sender, MouseButtonEventArgs e)
    {
        if (_viewModel == null) return;
        
        // Находим инвентаризацию, которая принадлежит нажатой карточке
        var border = sender as Border;
        if (border?.DataContext is RfidScanner.Models.Inventory inv)
        {
            _viewModel.SelectedInventory = inv;
            System.Diagnostics.Debug.WriteLine($"[InventoryCard_Click] Selected inventory: {inv.Name}");
        }
    }
    
    /// <summary>
    /// Предотвращает всплытие события от кнопки "Начать"
    /// </summary>
    private void Button_PreviewMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        e.Handled = true;
    }
    
    private static T? FindParent<T>(DependencyObject child) where T : DependencyObject
    {
        var parent = VisualTreeHelper.GetParent(child);
        if (parent == null) return null;
        return parent is T ? (T)parent : FindParent<T>(parent);
    }
}
