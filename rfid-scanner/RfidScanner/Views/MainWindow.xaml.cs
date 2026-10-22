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
    private readonly RoleService _roleService;
    private readonly AppUser _currentUser;
    private RoomSelectorView? _roomSelectorView;
    private bool _isSwitchingView;
    private Task? _finishTask;
    
    // Буфер для HID-сканера (посимвольный ввод)
    private readonly System.Text.StringBuilder _hidBuffer = new();
    private DateTime _lastHidKeyTime = DateTime.MinValue;

    // Максимальный интервал между символами одной метки (мс).
    // HID-ридер печатает всю метку потоком, поэтому пауза больше этой
    // значения означает начало новой метки / посторонний ввод.
    private const int HidCharTimeoutMs = 200;

    public MainWindow(ConfigService config, RoleService roleService, AppUser currentUser)
    {
        _config = config;
        _roleService = roleService;
        _currentUser = currentUser;
        config.Load();
        
        InitializeComponent();
        
        // Устанавливаем информацию о пользователе в верхней панели
        UpdateUserInfo();
        
        // Инициализация сервисов
        var localStore = new LocalStoreService();
        var auditService = new AuditService(localStore);
        auditService.SetCurrentUser(_currentUser.Username); // Устанавливаем текущего пользователя
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
        
        // Используем ViewModel из RoomSelectorView
        _roomSelectorViewModel = _roomSelectorView.ViewModel!;
        
        // ScanView создан в XAML
        _scanView = ScanHostView;
        _scanView.Visibility = System.Windows.Visibility.Collapsed;
        // Инициализируем ScanView сразу (до первой сессии), чтобы ItemsSource был привязан
        _scanView.Initialize(_scanViewModel);
        
        // Подписываемся на события
        _scanView.Finished += OnFinished;
        _scanView.InventoryCompleted += () =>
        {
            System.Diagnostics.Debug.WriteLine("[InventoryCompleted] Inventory completed, switching to room selector...");
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                SwitchToRoomSelector();
            });
        };
        
        _scanView.Reset += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                if (MessageBox.Show("Сбросить сессию? Все данные будут удалены.", 
                    "Подтверждение", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
                {
                    System.Diagnostics.Debug.WriteLine("[Reset] Resetting session...");
                    _sessionManager.ResetSession();
                    System.Diagnostics.Debug.WriteLine($"[Reset] After ResetSession: HasActiveSession={_sessionManager.HasActiveSession}, State={_sessionManager.CurrentSession?.State}");
                    SwitchToRoomSelector();
                }
            });
        };
        _scanView.Exit += () =>
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                System.Diagnostics.Debug.WriteLine("[Exit] EXIT BUTTON CLICKED");
                try
                {
                    // SwitchToRoomSelector reloads rooms + inventories
                    System.Diagnostics.Debug.WriteLine("[Exit] Switching view...");
                    SwitchToRoomSelector();
                    System.Diagnostics.Debug.WriteLine("[Exit] View switched successfully");
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[Exit] ERROR: {ex.GetType().Name}: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"[Exit] StackTrace: {ex.StackTrace}");
                }
            });
        };
        
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
        
        // HID-сканер
        PreviewKeyDown += MainWindow_PreviewKeyDown;
        
        // Подписка на создание сессии
        _sessionManager.SessionChanged += OnSessionCreated;
        
        // Статус по умолчанию
        ConnectionStatus.Text = "Проверка подключения...";
        ConnectionStatus.Foreground = System.Windows.Media.Brushes.Orange;
    }

    /// <summary>
    /// Обновляет отображение информации о текущем пользователе
    /// </summary>
    private void UpdateUserInfo()
    {
        var roleText = RoleService.GetRoleText(_currentUser.Role);
        var departmentText = string.IsNullOrEmpty(_currentUser.Department) 
            ? string.Empty 
            : $" | {_currentUser.Department}";
        
        ConnectionStatus.Text = $"👤 {_currentUser.Username} ({roleText}{departmentText})";
        ConnectionStatus.Foreground = System.Windows.Media.Brushes.White;
    }

    // ==================== Завершение инвентаризации ====================

    private void OnFinished()
    {
        if (_finishTask != null && !_finishTask.IsCompleted)
        {
            System.Diagnostics.Debug.WriteLine("[Finished] Already finishing, ignoring duplicate");
            return;
        }
        _finishTask = FinishInventoryAsync();
    }

    private async Task FinishInventoryAsync()
    {
        try
        {
            System.Diagnostics.Debug.WriteLine("[Finished] Starting inventory completion...");

            var result = await _scanViewModel.FinishWithSyncAsync();

            System.Diagnostics.Debug.WriteLine($"[Finished] FinishWithSync: Success={result.Success}, ServerError={result.ServerError}, Skipped={result.SkippedCount}");

            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                if (result.SkippedCount > 0)
                {
                    var msg = $"Инвентаризация завершена.\n\n" +
                              $"✅ Найдено: {_scanViewModel.MatchedCount}\n" +
                              $"❌ Отсутствует: {_scanViewModel.MissingCount}\n" +
                              $"⏭ Пропущено: {result.SkippedCount}\n\n";

                    if (result.ServerError)
                        msg += $"⚠ Ошибка сервера: {result.Message}";
                    else if (result.Success)
                        msg += "✅ Результаты отправлены на сервер.";

                    MessageBox.Show(msg, "Завершение инвентаризации",
                        MessageBoxButton.OK,
                        result.ServerError ? MessageBoxImage.Warning : MessageBoxImage.Information);
                }
                else if (result.ServerError)
                {
                    MessageBox.Show($"Инвентаризация завершена локально.\n\nОшибка: {result.Message}",
                        "Завершение инвентаризации", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
                else
                {
                    MessageBox.Show($"Инвентаризация завершена.\n\nНайдено: {_scanViewModel.MatchedCount}\nОтсутствует: {_scanViewModel.MissingCount}",
                        "Завершение инвентаризации", MessageBoxButton.OK, MessageBoxImage.Information);
                }

                SwitchToRoomSelector();
            });
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[Finished] ERROR: {ex.GetType().Name}: {ex.Message}");
            System.Diagnostics.Debug.WriteLine($"[Finished] StackTrace: {ex.StackTrace}");
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                MessageBox.Show($"Ошибка завершения инвентаризации:\n{ex.Message}",
                    "Ошибка", MessageBoxButton.OK, MessageBoxImage.Error);
                SwitchToRoomSelector();
            });
        }
        finally
        {
            _finishTask = null;
        }
    }

    private void OnSessionCreated(ScanSession session)
    {
        System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] State={session.State}, HasActiveSession={_sessionManager.HasActiveSession}");
        if (session.State == SessionState.Active)
        {
            System.Diagnostics.Debug.WriteLine("[OnSessionCreated] Calling Dispatcher.Invoke...");
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                try
                {
                    System.Diagnostics.Debug.WriteLine("[OnSessionCreated] Inside Dispatcher, switching to scan view...");
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
                        else
                        {
                            System.Diagnostics.Debug.WriteLine("[OnSessionCreated] ScanView already initialized");
                        }
                        
                        // Переключаем видимость — DataContext не меняем, каждый View имеет свой
                        _scanView.Visibility = System.Windows.Visibility.Visible;
                        _roomSelectorView.Visibility = System.Windows.Visibility.Collapsed;
                        
                        System.Diagnostics.Debug.WriteLine("[OnSessionCreated] ScanView shown, HasActiveSession=" + _sessionManager.HasActiveSession);
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
        else
        {
            System.Diagnostics.Debug.WriteLine($"[OnSessionCreated] SKIPPED: State={session.State}, HasActiveSession={_sessionManager.HasActiveSession}");
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
                _scanView.Visibility = System.Windows.Visibility.Visible;
                _roomSelectorView.Visibility = System.Windows.Visibility.Collapsed;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set ScanView (active session)");
                return;
            }
            
            // Если сессия завершена или нет активной сессии — показываем RoomSelector
            if (TabControl.SelectedIndex == 0)
            {
                System.Diagnostics.Debug.WriteLine($"[TabControl_SelectionChanged] HasActiveSession={_sessionManager.HasActiveSession}, SessionState={_sessionManager.CurrentSession?.State}");
                _scanView.Visibility = System.Windows.Visibility.Collapsed;
                _roomSelectorView.Visibility = System.Windows.Visibility.Visible;
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set RoomSelectorView");
            }
            else if (TabControl.SelectedIndex == 1)
            {
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set DataContext to SearchViewModel");
                DataContext = _searchViewModel;
            }
            else if (TabControl.SelectedIndex == 2)
            {
                System.Diagnostics.Debug.WriteLine("[TabControl_SelectionChanged] Set DataContext to AuditViewModel");
                DataContext = _auditViewModel;
                _auditViewModel.Refresh();
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

        // HID-сканер эмулирует клавиатуру: метка вводится ПОСИВОЛЬНО,
        // а в конце приходит Enter. Собираем символы в буфер и передаём
        // в ProcessTagCommand только целиком готовую метку (по Enter).
        var now = DateTime.Now;
        if ((now - _lastHidKeyTime).TotalMilliseconds > HidCharTimeoutMs)
            _hidBuffer.Clear(); // длинная пауза — начинаем новую метку
        _lastHidKeyTime = now;

        if (e.Key == Key.Return || e.Key == Key.Enter)
        {
            var tag = _hidBuffer.ToString().Trim();
            _hidBuffer.Clear();

            if (tag.Length > 0)
                _scanViewModel.ProcessTagCommand.Execute(tag);

            e.Handled = true;
            return;
        }

        var ch = KeyToChar(e.Key);
        if (ch != null)
        {
            _hidBuffer.Append(ch.Value);
            e.Handled = true;
        }
    }

    /// <summary>
    /// Преобразует клавишу в символ (для HID-сканера в режиме клавиатуры).
    /// Возвращает null, если клавиша не является частью метки.
    /// </summary>
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

    private void LogoutButton_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show("Вы действительно хотите выйти?\n\nВсе несохранённые данные будут потеряны.",
            "Выход", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
        {
            _roleService.Logout();
            Application.Current.Shutdown();
        }
    }

    private void SwitchToRoomSelector()
    {
        System.Diagnostics.Debug.WriteLine("[SwitchToRoomSelector] Switching to RoomSelectorView");
        _isSwitchingView = true;
        
        // Завершаем сессию ТОЛЬКО если она активна
        if (_sessionManager.HasActiveSession)
        {
            _sessionManager.FinishSession();
            System.Diagnostics.Debug.WriteLine("[SwitchToRoomSelector] Session finished during switch");
        }
        else
        {
            System.Diagnostics.Debug.WriteLine("[SwitchToRoomSelector] No active session, skipping finish");
        }
        
        _scanView.Visibility = System.Windows.Visibility.Collapsed;
        _roomSelectorView.Visibility = System.Windows.Visibility.Visible;
        _isSwitchingView = false;

        // По умолчанию показываем вкладки "Помещения" → "Начать инвентаризацию"
        _roomSelectorViewModel?.SetShowInventoriesList(false);
        // Reload data so completed inventories disappear from the active list
        _roomSelectorViewModel?.RefreshOnEnter();

        System.Diagnostics.Debug.WriteLine("[SwitchToRoomSelector] Done, data refresh requested");
    }
}
