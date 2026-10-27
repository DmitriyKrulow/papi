using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Controls;
using System.Windows.Media;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for MainWindow
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
    private readonly SearchView _searchView;
    private readonly AuditView _auditView;
    private readonly RoleService _roleService;
    private readonly AppUser _currentUser;
    private RoomSelectorView? _roomSelectorView;
    private bool _isSwitchingView;
    private Task? _finishTask;
    private bool _suppressSessionViewSwitch;
    private bool _wasInventoriesTab;
    
    // Буфер для HID-сканера (посимвольный ввод)
    private readonly System.Text.StringBuilder _hidBuffer = new();
    private DateTime _lastHidKeyTime = DateTime.MinValue;
    private const int HidCharTimeoutMs = 200;
    
    // Буфер для NFC-сканера (посимвольный ввод)
    private readonly System.Text.StringBuilder _nfcBuffer = new();
    private DateTime _lastNfcKeyTime = DateTime.MinValue;
    private const int NfcCharTimeoutMs = 200;

    public MainWindow(ConfigService config, RoleService roleService, AppUser currentUser)
    {
        _config = config;
        _roleService = roleService;
        _currentUser = currentUser;
        config.Load();
        
        InitializeComponent();
        
        // Устанавливаем информацию о пользователе
        UpdateUserInfo();
        
        // Инициализация сервисов
        var localStore = new LocalStoreService();
        var auditService = new AuditService(localStore);
        auditService.SetCurrentUser(_currentUser.Username);
        _assetCache = new AssetCacheService();
        _sessionManager = new SessionManager(localStore, auditService);
        var silentMode = new SilentModeService();
        var apiClient = new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey);
        
        _scanViewModel = new ScanViewModel(_sessionManager, silentMode, apiClient, localStore, _assetCache, _roleService);
        _searchViewModel = new SearchViewModel(apiClient, _assetCache);
        _auditViewModel = new AuditViewModel(localStore, _sessionManager);
        
        // RoomSelectorView создан в XAML — инициализируем
        _roomSelectorView = RoomSelectorHostView;
        _roomSelectorView.Initialize(apiClient, _sessionManager, _assetCache, auditService);
        _roomSelectorViewModel = _roomSelectorView.ViewModel!;
        
        // ScanView создан в XAML
        _scanView = ScanHostView;
        _scanView.Visibility = Visibility.Collapsed;
        _scanView.Initialize(_scanViewModel);
        
        // SearchView создан в XAML
        _searchView = SearchHostView;
        _searchView.Initialize(_searchViewModel);
        
        // AuditView создан в XAML
        _auditView = AuditHostView;
        _auditView.Initialize(_auditViewModel);
        
        // Подписываемся на события
        _scanView.Finished += OnFinished;
        _scanView.InventoryCompleted += () =>
        {
            Dispatcher.Invoke(() => SwitchToRoomSelector());
        };
        
        _scanView.Reset += () =>
        {
            Dispatcher.Invoke(() =>
            {
                if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
                    "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
                {
                    _sessionManager.ResetSession();
                    SwitchToRoomSelector();
                }
            });
        };
        
        _scanView.Exit += () =>
        {
            Dispatcher.Invoke(() => SwitchToRoomSelector());
        };
        
        // Подписка на загрузку помещений
        _roomSelectorView.ViewModel!.RoomsLoaded += () =>
        {
            Dispatcher.Invoke(() =>
            {
                UpdateWidgets();
                if (_roomSelectorView!.ViewModel!.Rooms.Count > 0)
                {
                    ConnectionStatus.Text = "Подключено к серверу";
                    ConnectionStatus.Foreground = (Brush)FindResource("ThemeSuccess");
                }
                else
                {
                    ConnectionStatus.Text = "Нет данных";
                    ConnectionStatus.Foreground = (Brush)FindResource("ThemeWarning");
                }
            });
        };
        
        // Подписка на загрузку инвентаризаций
        _roomSelectorView.ViewModel.InventoriesLoaded += () =>
        {
            Dispatcher.Invoke(() => UpdateWidgets());
        };
        
        // HID-сканер
        PreviewKeyDown += MainWindow_PreviewKeyDown;
        
        // Обновляем индикатор режима
        UpdateModeIndicator();
        
        // Подписка на создание сессии
        _sessionManager.SessionChanged += OnSessionCreated;
        
        // Статус по умолчанию
        ConnectionStatus.Text = "Проверка подключения...";
        ConnectionStatus.Foreground = (Brush)FindResource("ThemeWarning");
    }

    private void UpdateUserInfo()
    {
        var roleText = RoleService.GetRoleText(_currentUser.Role);
        var departmentText = string.IsNullOrEmpty(_currentUser.Department) 
            ? string.Empty 
            : $" | {_currentUser.Department}";
        
        UserDisplay.Text = $"{_currentUser.Username} ({roleText}{departmentText})";
    }

    /// <summary>
    /// Обновляет виджеты-сводки на главной странице
    /// </summary>
    private void UpdateWidgets()
    {
        if (_roomSelectorView?.ViewModel == null) return;

        var vm = _roomSelectorViewModel;
        
        // Показываем виджеты когда скан не активен
        WidgetsPanel.Visibility = ScanHostView.Visibility == Visibility.Collapsed 
            ? Visibility.Visible 
            : Visibility.Collapsed;
        
        // Обновляем числа виджетов
        WidgetRooms.Text = vm.Rooms.Count.ToString();
        WidgetActive.Text = vm.Inventories.Count.ToString();
    }

    // ==================== Навигация ====================

    private void NavInventory_Click(object sender, RoutedEventArgs e)
    {
        SetActiveNavItem(NavInventoryBtn);
        ShowView("inventory");
    }

    private void NavSearch_Click(object sender, RoutedEventArgs e)
    {
        SetActiveNavItem(NavSearchBtn);
        ShowView("search");
    }

    private void NavHistory_Click(object sender, RoutedEventArgs e)
    {
        SetActiveNavItem(NavHistoryBtn);
        ShowView("audit");
    }

    private void SetActiveNavItem(Button activeBtn)
    {
        NavInventoryBtn.Style = FindResource("SidebarNavItem") as Style;
        NavSearchBtn.Style = FindResource("SidebarNavItem") as Style;
        NavHistoryBtn.Style = FindResource("SidebarNavItem") as Style;
        
        activeBtn.Style = FindResource("SidebarNavActive") as Style;
    }

    private void ShowView(string viewName)
    {
        if (_isSwitchingView) return;
        _isSwitchingView = true;

        try
        {
            // Скрываем все
            RoomSelectorHostView.Visibility = Visibility.Collapsed;
            ScanHostView.Visibility = Visibility.Collapsed;
            SearchHostView.Visibility = Visibility.Collapsed;
            AuditHostView.Visibility = Visibility.Collapsed;

            // Показываем нужный
            switch (viewName)
            {
                case "inventory":
                    if (_sessionManager.HasActiveSession)
                    {
                        ScanHostView.Visibility = Visibility.Visible;
                    }
                    else
                    {
                        RoomSelectorHostView.Visibility = Visibility.Visible;
                        UpdateWidgets();
                    }
                    break;
                case "search":
                    SearchHostView.Visibility = Visibility.Visible;
                    _searchViewModel.SearchCommand.Execute(null);
                    break;
                case "audit":
                    AuditHostView.Visibility = Visibility.Visible;
                    _auditViewModel.Refresh();
                    break;
            }
        }
        finally
        {
            _isSwitchingView = false;
        }
    }

    // ==================== Переключение тем ====================

    private void ThemeToggle_Click(object sender, RoutedEventArgs e)
    {
        ThemeManager.Toggle(Application.Current);
        ToastService.Show(this, "Тема переключена", ToastType.Info);
    }

    // ==================== Завершение инвентаризации ====================

    private void OnFinished()
    {
        System.Diagnostics.Debug.WriteLine("[MainWindow] OnFinished called");
        if (_finishTask != null && !_finishTask.IsCompleted)
        {
            System.Diagnostics.Debug.WriteLine("[MainWindow] OnFinished - task already running, skipping");
            return;
        }
        System.Diagnostics.Debug.WriteLine("[MainWindow] Starting FinishInventoryAsync");
        _finishTask = FinishInventoryAsync();
    }

    private async Task FinishInventoryAsync()
    {
        try
        {
            System.Diagnostics.Debug.WriteLine("[MainWindow] Calling FinishWithSyncAsync");
            var result = await _scanViewModel.FinishWithSyncAsync();
            System.Diagnostics.Debug.WriteLine($"[MainWindow] FinishWithSyncAsync completed: Success={result.Success}, Skipped={result.SkippedCount}");

            // Показываем результат и переключаем view
            System.Diagnostics.Debug.WriteLine("[MainWindow] Showing toast and switching view");
            
            // Сбрасываем флаг подавления — он может остаться true от OnSessionCreated
            _suppressSessionViewSwitch = false;
            
            if (result.SkippedCount > 0)
            {
                var msg = $"Инвентаризация завершена.\n\n" +
                          $"✅ Найдено: {_scanViewModel.MatchedCount}\n" +
                          $"❌ Отсутствует: {_scanViewModel.MissingCount}\n" +
                          $"⏭ Пропущено: {result.SkippedCount}";

                if (result.ServerError)
                    ToastService.ShowWarning(this, $"⚠ Ошибка сервера: {result.Message}");
                else
                    ToastService.ShowSuccess(this, "✅ Результаты отправлены на сервер");
            }
            else if (result.ServerError)
            {
                ToastService.ShowWarning(this, $"Инвентаризация завершена локально. Ошибка: {result.Message}");
            }
            else
            {
                ToastService.ShowSuccess(this, $"Инвентаризация завершена. Найдено: {_scanViewModel.MatchedCount}, Отсутствует: {_scanViewModel.MissingCount}");
            }

            System.Diagnostics.Debug.WriteLine("[MainWindow] Calling SwitchToRoomSelector");
            SwitchToRoomSelector();
            System.Diagnostics.Debug.WriteLine("[MainWindow] SwitchToRoomSelector completed");
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[MainWindow] Exception in FinishInventoryAsync: {ex}");
            ToastService.ShowError(this, $"Ошибка завершения инвентаризации: {ex.Message}");
            SwitchToRoomSelector();
        }
        finally
        {
            _finishTask = null;
        }
    }

    // ==================== Сессия ====================

    private void OnSessionCreated(ScanSession session)
    {
        if (session.State == SessionState.Active)
        {
            Dispatcher.Invoke(() =>
            {
                if (!_isSwitchingView)
                {
                    _isSwitchingView = true;
                    _suppressSessionViewSwitch = true;
                    
                    if (_scanView.DataContext == null)
                        _scanView.Initialize(_scanViewModel);
                    
                    ScanHostView.Visibility = Visibility.Visible;
                    RoomSelectorHostView.Visibility = Visibility.Collapsed;
                    
                    // Разрешаем переключение через 500мс (после полной загрузки UI)
                    var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
                    timer.Tick += (s, e) =>
                    {
                        timer.Stop();
                        _suppressSessionViewSwitch = false;
                    };
                    timer.Start();
                }
                _isSwitchingView = false;
            });
        }
    }

    // ==================== HID-сканер ====================

    private void MainWindow_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        var focused = Keyboard.FocusedElement as TextBox;
        if (focused != null) return;
        if (Keyboard.FocusedElement is ComboBox) return;
        if (ScanHostView.Visibility != Visibility.Visible) return;

        var now = DateTime.Now;
        var isNfcMode = _config.Settings.ScannerMode == ScannerMode.Nfc;
        
        // Определяем какой буфер использовать
        var buffer = isNfcMode ? _nfcBuffer : _hidBuffer;
        var lastKeyTime = isNfcMode ? _lastNfcKeyTime : _lastHidKeyTime;
        var charTimeoutMs = isNfcMode ? NfcCharTimeoutMs : HidCharTimeoutMs;

        if ((now - lastKeyTime).TotalMilliseconds > charTimeoutMs)
            buffer.Clear();
        
        if (isNfcMode)
            _lastNfcKeyTime = now;
        else
            _lastHidKeyTime = now;

        if (e.Key == Key.Return || e.Key == Key.Enter)
        {
            var tag = buffer.ToString().Trim();
            buffer.Clear();

            if (tag.Length > 0)
            {
                var modeLabel = isNfcMode ? "NFC" : "RFID";
                System.Diagnostics.Debug.WriteLine($"[{modeLabel}] Tag: {tag}");
                _scanViewModel.ProcessTagCommand.Execute(tag);
            }

            e.Handled = true;
            return;
        }

        var ch = KeyToChar(e.Key);
        if (ch != null)
        {
            buffer.Append(ch.Value);
            e.Handled = true;
        }
    }

    private static char? KeyToChar(Key key)
    {
        if (key >= Key.A && key <= Key.Z)
            return (char)('a' + (key - Key.A));
        if (key >= Key.D0 && key <= Key.D9)
            return (char)('0' + (key - Key.D0));
        if (key >= Key.NumPad0 && key <= Key.NumPad9)
            return (char)('0' + (key - Key.NumPad0));
        return null;
    }

    private void UpdateModeIndicator()
    {
        var mode = _config.Settings.ScannerMode;
        switch (mode)
        {
            case ScannerMode.Nfc:
                ModeIndicator.Text = "📱 NFC";
                ModeIndicator.Foreground = (Brush)FindResource("ThemeSuccess");
                break;
            case ScannerMode.Serial:
                ModeIndicator.Text = "🔌 Serial";
                ModeIndicator.Foreground = (Brush)FindResource("ThemeWarning");
                break;
            case ScannerMode.Tcp:
                ModeIndicator.Text = "🌐 TCP";
                ModeIndicator.Foreground = (Brush)FindResource("ThemeInfo");
                break;
            default:
                ModeIndicator.Text = "📡 RFID";
                ModeIndicator.Foreground = (Brush)FindResource("ThemeAccentBright");
                break;
        }
    }

    // ==================== Кнопки ====================

    private void SkipButton_Click(object sender, RoutedEventArgs e)
    {
        _scanViewModel.SkipCommand.Execute(null);
    }

    private void FinishButton_Click(object sender, RoutedEventArgs e)
    {
        _sessionManager.FinishSession();
        SwitchToRoomSelector();
    }

    private void ResetButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
            "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
        {
            _sessionManager.ResetSession();
            SwitchToRoomSelector();
        }
    }

    private void SettingsButton_Click(object sender, RoutedEventArgs e)
    {
        var settingsWindow = new SettingsWindow(_config);
        settingsWindow.ShowDialog();
    }

    private void LogoutButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Вы действительно хотите выйти?\n\nВсе несохранённые данные будут потеряны.",
            "Выход", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
        {
            _roleService.Logout();
            Application.Current.Shutdown();
        }
    }

    // ==================== Переключение на выбор помещения ====================

    private void SwitchToRoomSelector()
    {
        System.Diagnostics.Debug.WriteLine("[MainWindow] SwitchToRoomSelector START");
        
        // Не переключаемся если только что создали сессию (защита от цикла)
        if (_suppressSessionViewSwitch)
        {
            System.Diagnostics.Debug.WriteLine("[MainWindow] SwitchToRoomSelector - suppressed");
            return;
        }
        
        // Сохраняем состояние вкладки перед завершением сессии
        _wasInventoriesTab = _roomSelectorViewModel?.ShowInventories ?? false;
        
        _isSwitchingView = true;
        
        if (_sessionManager.HasActiveSession)
        {
            System.Diagnostics.Debug.WriteLine("[MainWindow] Finishing session");
            _sessionManager.FinishSession();
        }
        
        ScanHostView.Visibility = Visibility.Collapsed;
        RoomSelectorHostView.Visibility = Visibility.Visible;
        _isSwitchingView = false;

        System.Diagnostics.Debug.WriteLine("[MainWindow] View switched to RoomSelector");
        
        // Восстанавливаем вкладку если была инвентаризация
        if (_wasInventoriesTab)
        {
            _roomSelectorViewModel?.SetShowInventoriesList(true);
            _roomSelectorViewModel?.LoadInventoriesCommand.Execute(null);
        }
        else
        {
            _roomSelectorViewModel?.SetShowInventoriesList(false);
            _roomSelectorViewModel?.LoadRoomsCommand.Execute(null);
        }
        
        UpdateWidgets();
        System.Diagnostics.Debug.WriteLine("[MainWindow] SwitchToRoomSelector DONE");
    }
}
