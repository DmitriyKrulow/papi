using System;
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

    public RoomSelectorView(RfidApiClient apiClient, SessionManager sessionManager, 
        AssetCacheService assetCache, AuditService audit, Action<ScanSession> onInventoryStarted)
    {
        _onInventoryStarted = onInventoryStarted;
        _sessionManager = sessionManager;
        
        InitializeComponent();
        
        _viewModel = new RoomSelectorViewModel(apiClient, sessionManager, assetCache, audit);
        DataContext = _viewModel;
        
        // Автоматическая загрузка помещений
        _viewModel.LoadRoomsCommand.Execute(null);
    }

    private void StartButton_Click(object sender, System.Windows.RoutedEventArgs e)
    {
        // Начать инвентаризацию
        _viewModel.StartInventoryCommand.Execute(null);
        
        // После успешного старта — перейти к сканированию
        if (_sessionManager.CurrentSession != null)
        {
            _onInventoryStarted(_sessionManager.CurrentSession);
        }
    }
}
