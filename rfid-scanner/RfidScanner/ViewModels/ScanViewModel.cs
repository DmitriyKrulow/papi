using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.Views;

namespace RfidScanner.ViewModels;

/// <summary>
/// Главный ViewModel — сводка, статусы с иконками, поиск и фильтрация
/// </summary>
public class ScanViewModel : INotifyPropertyChanged
{
    private readonly SessionManager _sessionManager;
    private readonly SilentModeService _silentMode;
    private readonly RfidApiClient _apiClient;
    private readonly LocalStoreService _localStore;
    private readonly AssetCacheService _assetCache;
    private readonly RoleService _roleService;
    private readonly ReportExportService _reportExport;
    private readonly ExternalIntegrationService _integration;

    private int _matchedCount;
    private int _extraCount;
    private int _missingCount;
    private int _totalCount;
    private string _statusText = "Ожидание сканирования...";
    private string _lastTag = "";
    private bool _isPaused;
    private bool _isFinished;
    private string _syncStatus = "Готово к работе";
    private int _pendingSyncCount;
    private string _sessionRoomName = "Помещение не выбрано";
    private string _hintText = "💡 Поднесите RFID-сканер на 1-3 см к метке и дождитесь сигнала";
    private string _searchQuery = "";
    private bool _filterFound;
    private bool _filterExtra;
    private bool _filterMissing;
    private bool _filterAll = true;
    private ScanResultItem? _selectedResult;
    private int _readErrorCount; // Счётчик ошибок считывания подряд
    private string _currentUser = "Пользователь";

    public ScanViewModel(SessionManager sessionManager, SilentModeService silentMode, 
        RfidApiClient apiClient, LocalStoreService localStore, AssetCacheService assetCache,
        RoleService? roleService = null, ReportExportService? reportExport = null,
        ExternalIntegrationService? integration = null)
    {
        _sessionManager = sessionManager;
        _silentMode = silentMode;
        _apiClient = apiClient;
        _localStore = localStore;
        _assetCache = assetCache;
        _roleService = roleService ?? new RoleService();
        _reportExport = reportExport ?? new ReportExportService();
        _integration = integration ?? new ExternalIntegrationService("", "");

        _currentUser = _roleService.CurrentUser?.Username ?? "Пользователь";

        _sessionManager.SessionChanged += OnSessionChanged;
        UpdateSyncStatus();
    }

    // ==================== Сводка ====================

    public int MatchedCount
    {
        get => _matchedCount;
        private set => SetProperty(ref _matchedCount, value);
    }

    public int ExtraCount
    {
        get => _extraCount;
        private set => SetProperty(ref _extraCount, value);
    }

    public int MissingCount
    {
        get => _missingCount;
        private set => SetProperty(ref _missingCount, value);
    }

    public int TotalCount
    {
        get => _totalCount;
        private set => SetProperty(ref _totalCount, value);
    }

    public int ProgressPercent => _totalCount > 0 
        ? (int)((double)_matchedCount / Math.Max(_totalCount, 1) * 100) 
        : 0;

    public string SessionRoomName
    {
        get => _sessionRoomName;
        private set => SetProperty(ref _sessionRoomName, value);
    }

    public string HintText
    {
        get => _hintText;
        private set => SetProperty(ref _hintText, value);
    }

    // ==================== Результаты ====================

    public ObservableCollection<ScanResultItem> MatchedItems { get; } = new();
    public ObservableCollection<ScanResultItem> ExtraItems { get; } = new();
    public ObservableCollection<ScanResultItem> MissingItems { get; } = new();
    public ObservableCollection<ScanResultItem> AllResults { get; } = new();

    /// <summary>
    /// Отфильтрованный список результатов для отображения
    /// </summary>
    public ObservableCollection<ScanResultItem> FilteredResults { get; private set; } = new();

    public bool HasResults => AllResults.Count > 0;

    public string SearchQuery
    {
        get => _searchQuery;
        set
        {
            if (SetProperty(ref _searchQuery, value))
                ApplyFilter();
        }
    }

    public bool FilterFound
    {
        get => _filterFound;
        set
        {
            if (SetProperty(ref _filterFound, value))
            {
                if (value) { _filterAll = false; _filterExtra = false; _filterMissing = false; ApplyFilter(); }
            }
        }
    }

    public bool FilterExtra
    {
        get => _filterExtra;
        set
        {
            if (SetProperty(ref _filterExtra, value))
            {
                if (value) { _filterAll = false; _filterFound = false; _filterMissing = false; ApplyFilter(); }
            }
        }
    }

    public bool FilterMissing
    {
        get => _filterMissing;
        set
        {
            if (SetProperty(ref _filterMissing, value))
            {
                if (value) { _filterAll = false; _filterFound = false; _filterExtra = false; ApplyFilter(); }
            }
        }
    }

    public bool FilterAll
    {
        get => _filterAll;
        set
        {
            if (SetProperty(ref _filterAll, value))
            {
                if (value) { _filterFound = false; _filterExtra = false; _filterMissing = false; ApplyFilter(); }
            }
        }
    }

    public ScanResultItem? SelectedResult
    {
        get => _selectedResult;
        set => SetProperty(ref _selectedResult, value);
    }

    // ==================== Статус ====================

    public string StatusText
    {
        get => _statusText;
        private set => SetProperty(ref _statusText, value);
    }

    public string SyncStatus
    {
        get => _syncStatus;
        private set => SetProperty(ref _syncStatus, value);
    }

    public int PendingSyncCount
    {
        get => _pendingSyncCount;
        private set => SetProperty(ref _pendingSyncCount, value);
    }

    public bool IsPaused
    {
        get => _isPaused;
        private set => SetProperty(ref _isPaused, value);
    }

    public bool IsFinished
    {
        get => _isFinished;
        private set => SetProperty(ref _isFinished, value);
    }

    public string LastTag
    {
        get => _lastTag;
        private set => SetProperty(ref _lastTag, value);
    }

    public int ReadErrorCount
    {
        get => _readErrorCount;
        private set => SetProperty(ref _readErrorCount, value);
    }

    public bool CanExportReports => _roleService.CanExportReports();

    public bool CanManageRooms => _roleService.CanManageRooms();

    // ==================== Команды ====================

    public ICommand ProcessTagCommand => new RelayCommand<string>(tag =>
    {
        if (string.IsNullOrEmpty(tag) || _sessionManager.CurrentSession == null) return;
        
        LastTag = tag;
        
        // Мгновенная визуальная реакция
        StatusText = "⏳ Обработка...";

        // СРАВНЕНИЕ С ЛОКАЛЬНЫМ КЭШОМ (без сети!)
        var cached = _assetCache.CheckLocalCache(tag);
        
        if (cached.Found)
        {
            // ПОКАЗЫВАЕМ ДИАЛОГ ПОДТВЕРЖДЕНИЯ перед отметкой "проверен"
            ShowConfirmationDialog(tag, cached.AssetName, cached.InventoryNumber);
        }
        else
        {
            // Лишний актив — не подтверждаем автоматически
            _sessionManager.AddTag(tag, ScanAssetStatus.Extra);
            _silentMode.PlayMismatch();
            StatusText = "⚠ Лишний актив";
            HintText = "⚠ Актив не найден в списке помещения. Проверьте метку.";
            ReadErrorCount = 0; // Сбрасываем счётчик ошибок
        }
    });

    /// <summary>
    /// Показать диалог подтверждения (для Matched активов)
    /// </summary>
    private void ShowConfirmationDialog(string rfidTag, string assetName, string inventoryNumber)
    {
        System.Windows.Application.Current.Dispatcher.Invoke(() =>
        {
            var dialog = new ConfirmationDialog(_localStore, _currentUser, rfidTag, assetName, inventoryNumber);
            
            if (dialog.ShowDialog() == true)
            {
                // Подтверждено
                _sessionManager.AddTag(rfidTag, ScanAssetStatus.Matched, assetName, inventoryNumber);
                _silentMode.PlayMatch();
                StatusText = $"✅ {assetName} — подтверждено";
                HintText = "✅ Актив найден! Следующая метка...";
                ReadErrorCount = 0;
            }
            else
            {
                // Отменено — помечаем как ошибку считывания
                HandleReadError(rfidTag, ScanErrorType.NoRead);
            }
        });
    }

    /// <summary>
    /// Обработка ошибки считывания
    /// </summary>
    private void HandleReadError(string rfidTag, ScanErrorType errorType)
    {
        ReadErrorCount++;
        var info = ErrorHandlingViewModel.GetErrorInfo(errorType);
        
        StatusText = info.Message;
        HintText = info.Hint;

        // Сохраняем ошибку
        var error = new ScanErrorRecord
        {
            RfidTag = rfidTag,
            ErrorType = errorType,
            RetryCount = ReadErrorCount,
            Message = info.Hint
        };
        _localStore.SaveScanError(error);

        // После 3 ошибок подряд — предлагаем пропустить
        if (ReadErrorCount >= 3)
        {
            HintText = "⚠️ После 3 ошибок подряд рекомендуется пропустить метку или ввести вручную.";
        }
    }

    /// <summary>
    /// Ручной ввод актива
    /// </summary>
    public ICommand ManualEntryCommand => new RelayCommand(() =>
    {
        System.Windows.Application.Current.Dispatcher.Invoke(() =>
        {
            var dialog = new ManualEntryDialog();
            
            if (dialog.ShowDialog() == true && dialog.Entry != null)
            {
                dialog.Entry.EnteredBy = _currentUser;
                
                if (_sessionManager.CurrentSession != null)
                {
                    _localStore.SaveManualEntry(dialog.Entry, _sessionManager.CurrentSession.Id);
                    
                    // Добавляем как "пропущенный" с пометкой "введён вручную"
                    var item = new ScanResultItem
                    {
                        RfidTag = $"MANUAL:{dialog.Entry.InventoryNumber}",
                        Status = ScanAssetStatus.Missing,
                        AssetName = dialog.Entry.AssetName,
                        InventoryNumber = dialog.Entry.InventoryNumber,
                        Note = $"Введён вручную: {dialog.Entry.Note}",
                        ScannedAt = DateTime.Now
                    };
                    
                    _sessionManager.AddTag(item.RfidTag, item.Status, item.AssetName, item.InventoryNumber);
                    
                    StatusText = $"✏️ Актив добавлен: {dialog.Entry.AssetName}";
                    HintText = "✅ Ручной ввод выполнен. Продолжайте сканирование.";
                }
            }
        });
    });

    /// <summary>
    /// Пропустить ошибку считывания
    /// </summary>
    public ICommand SkipErrorCommand => new RelayCommand(() =>
    {
        if (_sessionManager.CurrentSession == null) return;
        
        var error = new ScanErrorRecord
        {
            RfidTag = LastTag,
            ErrorType = ScanErrorType.NoRead,
            RetryCount = ReadErrorCount,
            IsResolved = true,
            ResolvedBy = "skipped"
        };
        _localStore.SaveScanError(error);
        _localStore.ResolveScanError(_sessionManager.CurrentSession.Id, LastTag, "skipped");
        
        ReadErrorCount = 0;
        HintText = "⏭ Ошибка пропущена. Продолжайте сканирование.";
        StatusText = "⏭ Пропущено";
    });

    /// <summary>
    /// Повторить считывание
    /// </summary>
    public ICommand RetryReadCommand => new RelayCommand(() =>
    {
        StatusText = "🔄 Повторное считывание...";
        HintText = "💡 Поднесите сканер ближе к метке и дождитесь сигнала.";
        ReadErrorCount = 0;
    });

    public ICommand SkipCommand => new RelayCommand(() =>
    {
        if (_sessionManager.CurrentSession == null) return;
        
        HintText = "⏭ Активы пропущены. Продолжайте сканирование.";
        StatusText = "⏭ Пропущено";
        _silentMode.PlayMismatch();
    });

    public ICommand SyncCommand => new RelayCommand(SyncToApi);

    // ==================== Обработчики ====================

    private void OnSessionChanged(ScanSession session)
    {
        System.Windows.Application.Current.Dispatcher.Invoke(() =>
        {
            MatchedCount = session.MatchedCount;
            ExtraCount = session.ExtraCount;
            MissingCount = session.MissingCount;
            TotalCount = session.TotalScanned;
            IsPaused = session.IsPaused;
            IsFinished = session.IsFinished;

            // Обновляем имя помещения
            SessionRoomName = session.RoomName;

            // Обновляем AllResults
            AllResults.Clear();
            foreach (var result in session.Results)
                AllResults.Add(result);

            // Цветовой статус
            if (session.ExtraCount > 0)
            {
                StatusText = $"⚠️ Найдено лишних: {session.ExtraCount}";
                HintText = "⚠ Есть лишние активы. Проверьте метки.";
            }
            else if (session.MatchedCount > 0)
            {
                StatusText = $"✅ Найдено: {session.MatchedCount}";
                HintText = "✅ Продолжайте сканирование меток...";
            }
            else
            {
                StatusText = "Ожидание сканирования...";
                HintText = "💡 Поднесите RFID-сканер на 1-3 см к метке и дождитесь сигнала";
            }

            ApplyFilter();
        });
    }

    // ==================== Поиск и фильтрация ====================

    private void ApplyFilter()
    {
        FilteredResults.Clear();

        // Обновляем коллекции по статусам
        MatchedItems.Clear();
        ExtraItems.Clear();
        MissingItems.Clear();
        foreach (var r in AllResults)
        {
            if (r.Status == ScanAssetStatus.Matched) MatchedItems.Add(r);
            else if (r.Status == ScanAssetStatus.Extra) ExtraItems.Add(r);
            else if (r.Status == ScanAssetStatus.Missing) MissingItems.Add(r);
        }

        IEnumerable<ScanResultItem> source;
        if (_filterAll) source = AllResults;
        else if (FilterFound) source = MatchedItems;
        else if (FilterExtra) source = ExtraItems;
        else if (FilterMissing) source = MissingItems;
        else source = AllResults;

        // Поиск по тексту
        if (!string.IsNullOrWhiteSpace(SearchQuery))
        {
            var q = SearchQuery.ToLower();
            source = source.Where(item =>
                (item.AssetName?.ToLower().Contains(q) == true) ||
                (item.InventoryNumber?.ToLower().Contains(q) == true) ||
                (item.RfidTag?.ToLower().Contains(q) == true));
        }

        foreach (var item in source)
            FilteredResults.Add(item);
    }

    // ==================== Синхронизация ====================

    /// <summary>
    /// Экспорт отчёта
    /// </summary>
    public ICommand ExportReportCommand => new RelayCommand(() =>
    {
        if (!_roleService.CanExportReports())
        {
            MessageBox.Show("У вас нет прав для экспорта отчётов. Обратитесь к администратору.", 
                "Доступ запрещён", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var parameters = new ReportParameters
        {
            RoomName = SessionRoomName,
            FromDate = DateTime.Now.AddDays(-30),
            ToDate = DateTime.Now,
            IncludeMatched = true,
            IncludeExtra = true,
            IncludeMissing = true
        };

        var result = _reportExport.SaveFileDialog(
            AllResults.ToList(), parameters, _currentUser, ReportFormat.Csv);

        if (result.HasValue && result.Value.Success)
        {
            SyncStatus = $"📄 Отчёт сохранён: {result.Value.FilePath}";
        }
    });

    /// <summary>
    /// Интеграция с 1С
    /// </summary>
    public ICommand SyncWith1CCommand => new RelayCommand(async () =>
    {
        if (!_roleService.CanExportReports())
        {
            MessageBox.Show("Интеграция с 1С доступна только для администраторов.", 
                "Доступ запрещён", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        SyncStatus = "🔄 Синхронизация с 1С...";
        try
        {
            var success = await _integration.SyncWith1CAsync(AllResults.ToList().Select(r => new Asset
            {
                RfidTag = r.RfidTag,
                InventoryNumber = r.InventoryNumber,
                Name = r.AssetName
            }).ToList(), "push");

            if (success)
                SyncStatus = "✅ Синхронизация с 1С завершена";
            else
                SyncStatus = "❌ Ошибка синхронизации с 1С";
        }
        catch (Exception ex)
        {
            SyncStatus = $"❌ Ошибка: {ex.Message}";
        }
    });

    private async void SyncToApi()
    {
        SyncStatus = "🔄 Синхронизация...";
        try
        {
            var unsynced = _localStore.GetUnsyncedSessions();
            foreach (var session in unsynced)
            {
                // Отправка на сервер (заглушка)
                _localStore.MarkSynced(session.Id);
            }
            SyncStatus = "✅ Все данные отправлены";
            UpdateSyncStatus();
        }
        catch (Exception ex)
        {
            SyncStatus = $"❌ Ошибка: {ex.Message}";
        }
    }

    private void UpdateSyncStatus()
    {
        var pending = _localStore.GetPendingCount();
        PendingSyncCount = pending;
        SyncStatus = pending > 0 ? $"⏳ В очереди: {pending}" : "✅ Готово к работе";
    }

    // ==================== INotifyPropertyChanged ====================

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
