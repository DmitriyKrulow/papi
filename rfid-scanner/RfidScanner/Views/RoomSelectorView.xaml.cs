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
    private readonly RoomSelectorViewModel _viewModel;
    private readonly SessionManager _sessionManager;
    private readonly Action<ScanSession> _onInventoryStarted;
    private TabControl? _tabControl;

    public RoomSelectorView(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit, Action<ScanSession> onInventoryStarted)
    {
        _onInventoryStarted = onInventoryStarted;
        _sessionManager = sessionManager;
        
        InitializeComponent();
        
        _viewModel = new RoomSelectorViewModel(apiClient, sessionManager, assetCache, audit, onInventoryStarted);
        DataContext = _viewModel;
        
        // Автоматическая загрузка помещений
        _viewModel.LoadRoomsCommand.Execute(null);
    }

    protected override void OnInitialized(EventArgs e)
    {
        base.OnInitialized(e);
        
        // Находим TabControl внутри UserControl
        _tabControl = RoomsTab.Parent as TabControl;
        if (_tabControl != null)
        {
            _tabControl.SelectionChanged += OnTabControlSelectionChanged;
        }
    }

    private void OnTabControlSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_tabControl?.SelectedItem is TabItem selectedTab)
        {
            if (selectedTab == RoomsTab)
                _viewModel.LoadRoomsCommand.Execute(null);
            else if (selectedTab == InventoriesTab)
                _viewModel.LoadInventoriesCommand.Execute(null);
        }
    }

    private void StartButton_Click(object sender, RoutedEventArgs e)
    {
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
