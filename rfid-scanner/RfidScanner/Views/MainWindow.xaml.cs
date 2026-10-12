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
    private readonly ScanView _scanView;
    private RoomSelectorView? _roomSelectorView;
    private bool _isSwitchingView;

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
        _roomSelectorViewModel = new RoomSelectorViewModel(apiClient, _sessionManager, _assetCache, auditService);
        
        // Создаём RoomSelectorView в коде
        _roomSelectorView = new RoomSelectorView();
        _roomSelectorView.Initialize(apiClient, _sessionManager, _assetCache, auditService);
        RoomSelectorHost.Content = _roomSelectorView;
        
        // Создаём ScanView для режима сканирования (не инициализируем здесь)
        _scanView = new ScanView();
        _scanView.Finished += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                _sessionManager.FinishSession();
                RoomSelectorHost.Content = _roomSelectorView;
                DataContext = _roomSelectorViewModel;
            });
        };
        _scanView.Reset += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
                    "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
                {
                    _sessionManager.ResetSession();
                    RoomSelectorHost.Content = _roomSelectorView;
                    DataContext = _roomSelectorViewModel;
                }
            });
        };
        _scanView.Exit += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                RoomSelectorHost.Content = _roomSelectorView;
                DataContext = _roomSelectorViewModel;
            });
        };
        
        // Привязка ViewModel к вкладкам
        DataContext = _roomSelectorViewModel;
        
        // HID-сканер
        PreviewKeyDown += MainWindow_PreviewKeyDown;
        
        // Подписка на создание сессии (из RoomSelectorViewModel)
        _sessionManager.SessionChanged += OnSessionCreated;
        
        // Статус по умолчанию
        ConnectionStatus.Text = "Проверка подключения...";
        ConnectionStatus.Foreground = System.Windows.Media.Brushes.Orange;
        
        // Подписка на загрузку помещений для обновления статуса
        if (_roomSelectorView?.ViewModel != null)
        {
            _roomSelectorView.ViewModel.RoomsLoaded += () =>
            {
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                {
                    if (_roomSelectorView.ViewModel!.Rooms.Count > 0)
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
    }

    private void OnSessionCreated(ScanSession session)
    {
        System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] State={session.State}, HasActiveSession={_sessionManager.HasActiveSession}");
        if (session.State == SessionState.Active)
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                try
                {
                    System.Diagnostics.Debug.WriteLine("[OnSessionCreated] Switching to scan view...");
                    if (!_isSwitchingView)
                    {
                        _isSwitchingView = true;
                        TabControl.SelectedIndex = 0;
                        
                        // Инициализируем ScanView при первом показе
                        if (_scanView.DataContext == null)
                        {
                            try
                            {
                                _scanView.Initialize(_scanViewModel);
                                System.Diagnostics.Debug.WriteLine("[OnSessionCreated] ScanView initialized");
                            }
                            catch (Exception ex)
                            {
                                System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] Init ERROR: {ex.Message}");
                            }
                        }
                        
                        // Меняем Content на ScanView
                        RoomSelectorHost.Content = _scanView;
                        DataContext = _scanViewModel;
                        
                        System.Diagnostics.Debug.WriteLine("[OnSessionCreated] ScanView shown");
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine("[OnSessionCreated] SKIPPED: Already switching");
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] ERROR: {ex.GetType().Name}: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] StackTrace: {ex.StackTrace}");
                    MessageBox.Show($"Ошибка переключения: {ex.Message}", "Ошибка", 
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
                finally
                {
                    _isSwitchingView = false;
                }
            });
        }
    }

    private void TabControl_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        System.Diagnostics.Debug.WriteLine($"[TabControl_SelectionChanged] SelectedIndex={TabControl.SelectedIndex}, IsSwitching={_isSwitchingView}, HasActiveSession={_sessionManager.HasActiveSession}");
        if (_isSwitchingView) 
        {
            System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] SKIPPED: IsSwitchingView=true");
            return;
        }
        _isSwitchingView = true;
        
        try
        {
            // Если активное сканирование — не переключать DataContext на room selector
            if (_sessionManager.HasActiveSession && TabControl.SelectedIndex == 0)
            {
                RoomSelectorHost.Content = _scanView;
                DataContext = _scanViewModel;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set ScanView (active session)");
                return;
            }
            
            if (TabControl.SelectedIndex == 0)
            {
                RoomSelectorHost.Content = _roomSelectorView;
                DataContext = _roomSelectorViewModel;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set RoomSelectorViewModel");
            }
            else if (TabControl.SelectedIndex == 1)
            {
                DataContext = _searchViewModel;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set DataContext to SearchViewModel");
            }
            else if (TabControl.SelectedIndex == 2)
            {
                DataContext = _auditViewModel;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set DataContext to AuditViewModel");
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[TabControl_SelectionChanged] ERROR: {ex.Message}");
        }
        finally
        {
            _isSwitchingView = false;
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
        RoomSelectorHost.Content = _roomSelectorView;
        DataContext = _roomSelectorViewModel;
    }

    private void ResetButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
            "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
        {
            _sessionManager.ResetSession();
            RoomSelectorHost.Content = _roomSelectorView;
            DataContext = _roomSelectorViewModel;
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
