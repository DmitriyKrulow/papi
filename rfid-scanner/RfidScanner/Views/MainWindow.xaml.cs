using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Controls;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    private readonly ConfigService _config;
    private readonly SessionManager _sessionManager;
    private readonly AssetCacheService _assetCache;
    private readonly ScanViewModel _scanViewModel;
    private readonly SearchViewModel _searchViewModel;
    private readonly AuditViewModel _auditViewModel;
    private readonly RoomSelectorViewModel _roomSelectorViewModel;

    public MainWindow(ConfigService config)
    {
        _config = config;
        config.Load();
        
        InitializeComponent();
        
        // Инициализация сервисов
        var localStore = new LocalStoreService();
        var auditService = new AuditService(localStore);
        _assetCache = new AssetCacheService();
        _sessionManager = new SessionManager(localStore, auditService);
        var silentMode = new SilentModeService();
        var apiClient = new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey);
        
        _scanViewModel = new ScanViewModel(_sessionManager, silentMode, apiClient, localStore, _assetCache);
        _searchViewModel = new SearchViewModel(apiClient, _assetCache);
        _auditViewModel = new AuditViewModel(localStore, _sessionManager);
        _roomSelectorViewModel = new RoomSelectorViewModel(apiClient, _sessionManager, _assetCache, auditService, OnSessionCreated);
        
        // Создаём RoomSelectorView в коде
        var roomSelectorView = new RoomSelectorView();
        roomSelectorView.Initialize(apiClient, _sessionManager, _assetCache, auditService, OnSessionCreated);
        RoomSelectorHost.Content = roomSelectorView;
        
        // Привязка ViewModel к вкладкам
        DataContext = _roomSelectorViewModel;
        
        // HID-сканер
        PreviewKeyDown += MainWindow_PreviewKeyDown;
        
        // Подписка на создание сессии
        _sessionManager.SessionChanged += OnSessionCreated;
        
        // Статус по умолчанию
        ConnectionStatus.Text = "Проверка подключения...";
        ConnectionStatus.Foreground = System.Windows.Media.Brushes.Orange;
        
        // Загрузка помещений и инвентаризаций происходит в RoomSelectorView.Initialize()
        
        // Подписка на загрузку помещений для обновления статуса
        _roomSelectorViewModel.RoomsLoaded += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                if (_roomSelectorViewModel.Rooms.Count > 0)
                {
                    ConnectionStatus.Text = "Подключено";
                    ConnectionStatus.Foreground = System.Windows.Media.Brushes.Green;
                }
                else
                {
                    ConnectionStatus.Text = "Нет данных";
                    ConnectionStatus.Foreground = System.Windows.Media.Brushes.Orange;
                }
            });
        };
    }

    private void OnSessionCreated(ScanSession session)
    {
        if (session.State == SessionState.Active)
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                TabControl.SelectedIndex = 0;
                DataContext = _scanViewModel;
            });
        }
    }

    private void TabControl_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (TabControl.SelectedIndex == 0)
        {
            DataContext = _roomSelectorViewModel;
        }
        else if (TabControl.SelectedIndex == 1)
        {
            DataContext = _searchViewModel;
        }
        else if (TabControl.SelectedIndex == 2)
        {
            DataContext = _auditViewModel;
        }
    }

    private void MainWindow_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        // Если фокус в TextBox — пропускаем ввод
        var focused = Keyboard.FocusedElement as TextBox;
        if (focused != null) return;
        
        if (Keyboard.FocusedElement is ComboBox) return;
        
        // Только если активна вкладка "Инвентаризация"
        if (TabControl.SelectedIndex != 0) return;
        
        if (e.Key >= Key.D0 && e.Key <= Key.Z)
        {
            var charCode = char.ToLower((char)e.Key);
            _scanViewModel.ProcessTagCommand.Execute(charCode.ToString());
            e.Handled = true;
        }
        else if (e.Key >= Key.NumPad0 && e.Key <= Key.NumPad9)
        {
            var charCode = (char)(e.Key - Key.NumPad0 + '0');
            _scanViewModel.ProcessTagCommand.Execute(charCode.ToString());
            e.Handled = true;
        }
        else if (e.Key == Key.Return || e.Key == Key.Enter)
        {
            _scanViewModel.ProcessTagCommand.Execute(string.Empty);
            e.Handled = true;
        }
    }

    private void SkipButton_Click(object sender, RoutedEventArgs e)
    {
        _scanViewModel.SkipCommand.Execute(null);
    }

    private void FinishButton_Click(object sender, RoutedEventArgs e)
    {
        _sessionManager.FinishSession();
    }

    private void ResetButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
            "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
        {
            _sessionManager.ResetSession();
        }
    }

    private void SearchButton_Click(object sender, RoutedEventArgs e)
    {
        TabControl.SelectedIndex = 1;
        DataContext = _searchViewModel;
        _searchViewModel.SearchCommand.Execute(null);
    }

    private void SearchBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            _searchViewModel.SearchCommand.Execute(null);
        }
    }

    private void HistoryButton_Click(object sender, RoutedEventArgs e)
    {
        TabControl.SelectedIndex = 2;
        DataContext = _auditViewModel;
        _auditViewModel.Refresh();
    }

    private void RefreshHistory_Click(object sender, RoutedEventArgs e)
    {
        _auditViewModel.Refresh();
    }

    private void SettingsButton_Click(object sender, RoutedEventArgs e)
    {
        var settingsWindow = new SettingsWindow(_config);
        settingsWindow.ShowDialog();
    }
}
