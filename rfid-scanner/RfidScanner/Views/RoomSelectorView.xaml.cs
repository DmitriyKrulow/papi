using System.Windows;
using System.Windows.Controls;
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
    private TabControl? _tabControl;
    private bool _isInitialized;

    /// <summary>
    /// ViewModel для подписки на события из MainWindow
    /// </summary>
    public RoomSelectorViewModel? ViewModel => _viewModel;

    public RoomSelectorView()
    {
        InitializeComponent();
    }

    public void Initialize(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit)
    {
        _sessionManager = sessionManager;
        
        _viewModel = new RoomSelectorViewModel(apiClient, sessionManager, assetCache, audit);
        DataContext = _viewModel;
        
        // Вкладка "Помещения" выбрана по умолчанию → кнопка "Начать инвентаризацию"
        _viewModel.SetShowInventoriesList(false);
        
        // Автоматическая загрузка помещений и инвентаризаций
        _viewModel.LoadRoomsCommand.Execute(null);
        _viewModel.LoadInventoriesCommand.Execute(null);
    }

    protected override void OnInitialized(EventArgs e)
    {
        base.OnInitialized(e);
        
        // Находим TabControl внутри UserControl
        _tabControl = RoomsTab.Parent as TabControl;
        if (_tabControl != null && !_isInitialized)
        {
            _tabControl.SelectionChanged += OnTabControlSelectionChanged;
            _isInitialized = true;
        }
    }

    private void OnTabControlSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_viewModel == null) return;
        // Если ничего не добавлено — значит кликнули по элементу внутри вкладки, а не переключили вкладку
        if (e.AddedItems.Count == 0) return;
        
        // Если ничего не удалено — вкладка не менялась, просто кликнули по элементу
        if (e.RemovedItems.Count == 0) return;
        
        // Теперь проверяем что это именно TabItem
        if (e.AddedItems[0] is not TabItem addedTab) return;
        
        // Вкладка определяет режим: Помещения → начать, Инвентаризации → продолжить
        _viewModel.SetShowInventoriesList(addedTab == InventoriesTab);
        
        if (addedTab == RoomsTab)
            _viewModel.LoadRoomsCommand.Execute(null);
        else if (addedTab == InventoriesTab)
            _viewModel.LoadInventoriesCommand.Execute(null);
    }

    private void StartButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        System.Diagnostics.Debug.WriteLine($"[StartButton_Click] ShowInventories={_viewModel.ShowInventories}, SelectedInventory={_viewModel.SelectedInventory?.Name ?? "null"}");
        
        if (_viewModel.ShowInventories)
        {
            _viewModel.ContinueInventoryCommand.Execute(null);
        }
        else
        {
            _viewModel.StartInventoryCommand.Execute(null);
        }
    }
}
