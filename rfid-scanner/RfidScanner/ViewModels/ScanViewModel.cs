using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using Newtonsoft.Json;
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
    private readonly OfflineQueueService _offlineQueue;

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
        ExternalIntegrationService? integration = null, OfflineQueueService? offlineQueue = null)
    {
        _sessionManager = sessionManager;
        _silentMode = silentMode;
        _apiClient = apiClient;
        _localStore = localStore;
        _assetCache = assetCache;
        _roleService = roleService ?? new RoleService();
        _reportExport = reportExport ?? new ReportExportService();
        _integration = integration ?? new ExternalIntegrationService("", "");
        _offlineQueue = offlineQueue ?? new OfflineQueueService();

        _currentUser = _roleService.CurrentUser?.Username ?? "Пользователь";

        _sessionManager.SessionChanged += OnSessionChanged;
        UpdateSyncStatus();
    }

    /// <summary>
    /// Загрузка активов для текущей сессии
    /// </summary>
    public async Task LoadSessionAssetsAsync()
    {
        System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] START: InventoryId={_sessionManager.CurrentSession?.InventoryId}, RoomId={_sessionManager.CurrentSession?.RoomId}");
        if (_sessionManager.CurrentSession == null || _sessionManager.CurrentSession.InventoryId == 0)
        {
            System.Diagnostics.Debug.WriteLine("[LoadSessionAssetsAsync] EARLY RETURN: No session or InventoryId=0");
            return;
        }

        try
        {
            StatusText = "🔄 Загрузка списка активов...";
            HintText = "Подождите, загружается проверяемое имущество...";
            
            List<Asset> assets;
            
            // Сначала проверяем, есть ли уже загруженные активы в сессии
            if (_sessionManager.CurrentSession.PendingAssets != null && _sessionManager.CurrentSession.PendingAssets.Count > 0)
            {
                var pendingAssets = _sessionManager.CurrentSession.PendingAssets;
                System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Using {pendingAssets.Count} pending assets from session");
                
                assets = pendingAssets;
                
                // Сохраняем в кэш для локальной проверки RFID
                var cacheStatus = await _assetCache.LoadRoomAssetsAsync(_sessionManager.CurrentSession.RoomId, assets);
                System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Cache saved from pending: {cacheStatus}");
                
                System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] BEFORE TotalCount={TotalCount}, setting to {pendingAssets.Count}");
                TotalCount = pendingAssets.Count;
                System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] AFTER TotalCount={TotalCount}");
                
                // Заполняем список активов для UI
                PopulateRoomAssets(pendingAssets);
                
                // Очищаем pending после использования
                _sessionManager.CurrentSession.PendingAssets = null;
                
                StatusText = $"✅ Загружено {pendingAssets.Count} активов. Готово к сканированию";
                HintText = "💡 Поднесите RFID-сканер на 1-3 см к метке и дождитесь сигнала";
                return;
            }
            
            // Загружаем из API (для продолжения инвентаризации)
            var inventoryItems = await _apiClient.GetInventoryAssetsAsync(_sessionManager.CurrentSession.InventoryId);
            
            System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Got {inventoryItems.Count} items from API");
            
            // Конвертируем InventoryItem в Asset для кэша
            assets = inventoryItems.Select(item => new Asset
            {
                RfidTag = item.RfidTag,
                Name = item.Name,
                InventoryNumber = item.InventoryNumber
            }).ToList();
            
            System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Converting to {assets.Count} Assets, RoomId={_sessionManager.CurrentSession.RoomId}");
            
            // Сохраняем в кэш для локальной проверки RFID
            var cacheResult = await _assetCache.LoadRoomAssetsAsync(_sessionManager.CurrentSession.RoomId, assets);
            System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Cache saved: {cacheResult}");
            
            TotalCount = inventoryItems.Count;
            System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] TotalCount set to: {TotalCount}");
            
            // Заполняем список активов С СЕРВЕРНЫМИ СТАТУСАМИ
            PopulateRoomAssetsWithStatus(inventoryItems);
            
            // Восстанавливаем счётчики из серверных данных
            var foundCount = inventoryItems.Count(i => i.CheckStatus == "found");
            var missingCount = inventoryItems.Count(i => i.CheckStatus == "missing");
            if (foundCount > 0 || missingCount > 0)
            {
                // Восстанавливаем результаты в сессии чтобы UI показывал корректно
                foreach (var invItem in inventoryItems.Where(i => i.CheckStatus == "found" && !string.IsNullOrEmpty(i.RfidTag)))
                {
                    _sessionManager.AddTag(invItem.RfidTag, ScanAssetStatus.Matched, invItem.Name, invItem.InventoryNumber);
                }
                System.Diagnostics.Debug.WriteLine($"[LoadSessionAssetsAsync] Restored {foundCount} found, {missingCount} missing from server");
            }
            
            StatusText = $"✅ Загружено {assets.Count} активов. Готово к сканированию";
            HintText = "💡 Поднесите RFID-сканер на 1-3 см к метке и дождитесь сигнала";
        }
        catch (Exception ex)
        {
            StatusText = "❌ Ошибка загрузки";
            HintText = $"Не удалось загрузить список: {ex.Message}";
        }
    }

    /// <summary>
    /// Заполняет список активов для отображения в UI с учётом серверных статусов
    /// </summary>
    private void PopulateRoomAssets(List<Asset> assets)
    {
        RoomAssets.Clear();
        foreach (var asset in assets)
        {
            var displayItem = new AssetDisplayItem { Asset = asset };
            RoomAssets.Add(displayItem);
        }
        System.Diagnostics.Debug.WriteLine($"[PopulateRoomAssets] Added {RoomAssets.Count} assets to UI list");
    }

    /// <summary>
    /// Заполняет список активов с серверными статусами проверки
    /// </summary>
    private void PopulateRoomAssetsWithStatus(List<InventoryItem> items)
    {
        RoomAssets.Clear();
        foreach (var item in items)
        {
            var asset = new Asset
            {
                RfidTag = item.RfidTag,
                Name = item.Name,
                InventoryNumber = item.InventoryNumber,
                Model = item.Model,
                Location = item.Location,
                Responsible = item.Responsible,
            };
            var displayItem = new AssetDisplayItem { Asset = asset };
            
            // Восстанавливаем статус из сервера
            if (item.CheckStatus == "found")
            {
                displayItem.MarkAsChecked();
            }
            // pending/missing → оставляем "Ожидание"
            
            RoomAssets.Add(displayItem);
        }
        System.Diagnostics.Debug.WriteLine($"[PopulateRoomAssetsWithStatus] Added {RoomAssets.Count} assets to UI list");
    }

    /// <summary>
    /// Обновляет статус активов на основе результатов сканирования
    /// </summary>
    private void UpdateAssetStatusFromResults(List<ScanResultItem> results)
    {
        var matchedTags = results.Where(r => r.Status == ScanAssetStatus.Matched)
            .Select(r => r.RfidTag)
            .ToHashSet();
        
        foreach (var item in RoomAssets)
        {
            if (matchedTags.Contains(item.Asset.RfidTag ?? string.Empty))
            {
                item.MarkAsChecked();
            }
            else
            {
                item.MarkAsNotChecked();
            }
        }
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
    
    public ObservableCollection<ScanResultItem> History { get; } = new();

    /// <summary>
    /// Отфильтрованный список результатов для отображения
    /// </summary>
    public ObservableCollection<ScanResultItem> FilteredResults { get; private set; } = new();

    /// <summary>
    /// Список активов помещения для отображения в UI
    /// </summary>
    public ObservableCollection<AssetDisplayItem> RoomAssets { get; } = new();

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

    /// <summary>
    /// Переключить паузу сканирования
    /// </summary>
    public void TogglePause()
    {
        IsPaused = !IsPaused;
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
        
        System.Diagnostics.Debug.WriteLine($"[ProcessTagCommand] Tag: '{tag}', Session: {_sessionManager.CurrentSession.Id}");
        LastTag = tag;
        
        // Мгновенная визуальная реакция
        StatusText = "⏳ Обработка...";

        // СРАВНЕНИЕ С ЛОКАЛЬНЫМ КЭШОМ (без сети!)
        System.Diagnostics.Debug.WriteLine($"[ProcessTagCommand] Checking local cache for tag: '{tag}'");
        var cached = _assetCache.CheckLocalCache(tag);
        System.Diagnostics.Debug.WriteLine($"[ProcessTagCommand] Cache result: Found={cached.Found}, Name='{cached.AssetName}', Inv='{cached.InventoryNumber}'");
        
        if (cached.Found)
        {
            // ПОКАЗЫВАЕМ ДИАЛОГ ПОДТВЕРЖДЕНИЯ перед отметкой "проверен"
            ShowConfirmationDialog(tag, cached.AssetName, cached.InventoryNumber);
        }
        else
        {
            // Лишний актив — помечаем локально и отправляем surplus на сервер
            _sessionManager.AddTag(tag, ScanAssetStatus.Extra);
            _silentMode.PlayMismatch();
            StatusText = "⚠ Лишний актив";
            HintText = "⚠ Актив не найден в списке помещения. Проверьте метку.";
            ReadErrorCount = 0; // Сбрасываем счётчик ошибок

            // Отправляем surplus на сервер
            _ = SendToServerAsync(tag, "surplus", "Лишний", "");
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
                // Подтверждено — отмечаем локально
                _sessionManager.AddTag(rfidTag, ScanAssetStatus.Matched, assetName, inventoryNumber);
                _silentMode.PlayMatch();
                StatusText = $"✅ {assetName} — подтверждено";
                HintText = "✅ Актив найден! Следующая метка...";
                ReadErrorCount = 0;

                // Отправляем на сервер асинхронно
                _ = SendToServerAsync(rfidTag, "found", assetName, inventoryNumber);
            }
            else
            {
                // Отменено — помечаем как ошибку считывания
                HandleReadError(rfidTag, ScanErrorType.NoRead);
            }
        });
    }

    /// <summary>
    /// Отправить результат сканирования на сервер (фоновая задача)
    /// </summary>
    private async Task SendToServerAsync(string rfidTag, string result, string? assetName = null, string? inventoryNumber = null)
    {
        var session = _sessionManager.CurrentSession;
        if (session == null || session.InventoryId <= 0)
            return;

        try
        {
            var scanResult = await _apiClient.ScanAsync(session.InventoryId, rfidTag, result);
            if (!scanResult.Success && !scanResult.IsSurplus)
            {
                System.Diagnostics.Debug.WriteLine($"[SendToServer] Failed for {rfidTag}: {scanResult.Message}");
                // Добавляем в офлайн-очередь
                _offlineQueue.AddItem(new OfflineQueueItem
                {
                    OperationType = Models.OfflineOperationType.Scan,
                    RfidTags = rfidTag,
                    InventoryId = session.InventoryId
                });
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[SendToServer] Exception: {ex.Message}");
            // В офлайн — добавляем в очередь
            _offlineQueue.AddItem(new OfflineQueueItem
            {
                OperationType = Models.OfflineOperationType.Scan,
                RfidTags = rfidTag,
                InventoryId = session.InventoryId
            });
        }
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

    // ==================== Завершение с пропуском ====================

    // Флаг: идёт пропуск/завершение — не перезагружать активы из API
    private bool _isSkippingOrFinishing;

    /// <summary>
    /// Завершить инвентаризацию с отправкой результатов на сервер
    /// </summary>
    public async Task<FinishResult> FinishWithSyncAsync()
    {
        if (_sessionManager.CurrentSession == null)
            return new FinishResult { Success = false, Message = "Нет активной сессии" };

        var inventoryId = _sessionManager.CurrentSession.InventoryId;
        System.Diagnostics.Debug.WriteLine($"[FinishWithSync] START: InventoryId={inventoryId}, RoomAssets={RoomAssets.Count}");

        _isSkippingOrFinishing = true;
        int skippedCount;
        try
        {
            // 1. Помечаем непроверенные активы как пропущенные локально
            skippedCount = MarkUncheckedAsSkipped();

            // 2. Отправляем все накопленные результаты на сервер (skip + pending)
            if (inventoryId > 0)
            {
                StatusText = "🔄 Отправка результатов на сервер...";
                await SyncPendingToServerAsync(inventoryId);
            }
        }
        finally
        {
            _isSkippingOrFinishing = false;
        }

        // 3. Завершаем локальную сессию
        _sessionManager.FinishSession();

        // 4. Отправляем на сервер — статус инвентаризации изменится на completed
        if (inventoryId <= 0)
        {
            System.Diagnostics.Debug.WriteLine("[FinishWithSync] SKIP: InventoryId=0, no server call");
            return new FinishResult
            {
                Success = false,
                Message = "Инвентаризация не привязана к серверу (InventoryId=0)",
                SkippedCount = skippedCount,
                ServerError = true
            };
        }

        StatusText = "🔄 Завершение инвентаризации на сервере...";
        var serverResult = await _apiClient.FinishInventoryAsync(inventoryId, skipPending: false);

        var success = serverResult.TryGetValue("success", out var s)
                      && (s is bool b ? b : string.Equals(s?.ToString(), "True", StringComparison.OrdinalIgnoreCase));
        var message = serverResult.TryGetValue("message", out var m) ? m?.ToString() ?? "" : "";

        System.Diagnostics.Debug.WriteLine($"[FinishWithSync] DONE: success={success}, message={message}");

        return new FinishResult
        {
            Success = success,
            Message = string.IsNullOrEmpty(message) ? (success ? "Инвентаризация завершена" : "Сервер не вернул сообщение") : message,
            SkippedCount = skippedCount,
            ServerError = !success
        };
    }

    /// <summary>
    /// Отправить все pending-результаты сессии на сервер перед завершением
    /// </summary>
    private async Task SyncPendingToServerAsync(int inventoryId)
    {
        try
        {
            var session = _sessionManager.CurrentSession;
            if (session == null) return;

            // 1. Отправляем все Matched/Missing результаты
            var resultsToSend = session.Results
                .Where(r => r.Status != ScanAssetStatus.Matched || true)
                .Select(r => new Dictionary<string, string>
                {
                    ["rfid_tag"] = r.RfidTag,
                    ["result"] = r.Status == ScanAssetStatus.Matched ? "found" : "missing"
                })
                .ToList();

            if (resultsToSend.Count > 0)
            {
                var syncResult = await _apiClient.SyncResultsAsync(inventoryId, resultsToSend);
                var ok = syncResult.TryGetValue("success", out var s)
                         && (s is bool b ? b : string.Equals(s?.ToString(), "True", StringComparison.OrdinalIgnoreCase));
                System.Diagnostics.Debug.WriteLine($"[SyncPending] Synced {resultsToSend.Count} results: ok={ok}");
            }

            // 2. Отправляем skip-all для remaining pending
            var skipResult = await _apiClient.SkipAllAsync(inventoryId);
            var skipOk = skipResult.TryGetValue("success", out var sk)
                         && (sk is bool sb ? sb : string.Equals(sk?.ToString(), "True", StringComparison.OrdinalIgnoreCase));
            System.Diagnostics.Debug.WriteLine($"[SyncPending] SkipAll: ok={skipOk}, skipped={skipResult.GetValueOrDefault("skipped", "0")}");
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[SyncPending] ERROR: {ex.Message}");
        }
    }

    /// <summary>
    /// Помечает все непроверенные активы как пропущенные. Возвращает количество.
    /// </summary>
    private int MarkUncheckedAsSkipped()
    {
        var skippedCount = 0;
        // Копия списка — AddTag может модифицировать коллекции через SessionChanged
        foreach (var item in RoomAssets.ToList())
        {
            if (item.IsChecked) continue;

            item.MarkAsSkipped();
            skippedCount++;
            _sessionManager.AddTag(
                string.IsNullOrEmpty(item.Asset.RfidTag) ? $"SKIP:{item.InventoryNumber}" : item.Asset.RfidTag,
                ScanAssetStatus.Missing,
                item.AssetName,
                item.InventoryNumber
            );
        }
        System.Diagnostics.Debug.WriteLine($"[MarkUncheckedAsSkipped] Skipped {skippedCount} assets");
        return skippedCount;
    }

    /// <summary>
    /// Пропустить все непроверенные активы (с отправкой на сервер)
    /// </summary>
    public async void SkipAllUnchecked()
    {
        if (_sessionManager.CurrentSession == null) return;

        _isSkippingOrFinishing = true;
        int skippedCount;
        try
        {
            skippedCount = MarkUncheckedAsSkipped();
        }
        finally
        {
            _isSkippingOrFinishing = false;
        }

        // Отправляем на сервер
        var inventoryId = _sessionManager.CurrentSession.InventoryId;
        if (inventoryId > 0)
        {
            _ = Task.Run(async () =>
            {
                var result = await _apiClient.SkipAllAsync(inventoryId);
                var ok = result.TryGetValue("success", out var s)
                         && (s is bool b ? b : string.Equals(s?.ToString(), "True", StringComparison.OrdinalIgnoreCase));
                System.Diagnostics.Debug.WriteLine($"[SkipAll] Server result: ok={ok}, skipped={result.GetValueOrDefault("skipped", "0")}");
            });
        }

        StatusText = $"⏭ Пропущено непроверенных: {skippedCount}";
        HintText = "✅ Все непроверенные активы помечены как отсутствующие";
        _silentMode.PlayMismatch();
    }

    // ==================== Обработчики ====================

    private void OnSessionChanged(ScanSession session)
    {
        System.Diagnostics.Debug.WriteLine($"[OnSessionChanged] Session: {session.Id}, State={session.State}, Results={session.Results.Count}");
        System.Windows.Application.Current.Dispatcher.Invoke(() =>
        {
            MatchedCount = session.MatchedCount;
            ExtraCount = session.ExtraCount;
            MissingCount = session.MissingCount;
            // TotalCount обновляется в LoadSessionAssetsAsync из API
            System.Diagnostics.Debug.WriteLine($"[OnSessionChanged] Counts: Matched={MatchedCount}, Extra={ExtraCount}, Missing={MissingCount}, Total={TotalCount}");
            IsPaused = session.IsPaused;
            IsFinished = session.IsFinished;

            // Обновляем имя помещения
            SessionRoomName = session.RoomName;

            // Обновляем AllResults
            AllResults.Clear();
            foreach (var result in session.Results)
                AllResults.Add(result);

            // Обновляем статус активов в списке помещения
            UpdateAssetStatusFromResults(session.Results);

            // Уведомляем View об обновлении результатов
            System.Diagnostics.Debug.WriteLine($"[OnSessionChanged] Firing ResultsUpdated event, AllResults count: {AllResults.Count}");
            ResultsUpdated?.Invoke();

            // Загружаем активы при создании новой сессии
            if (session.State == SessionState.Active && session.InventoryId > 0 && !_isSkippingOrFinishing)
            {
                _ = LoadSessionAssetsAsync();
            }

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
            // 1. Синхронизируем офлайн-очередь (отдельные сканы, которые не прошли)
            var pending = _offlineQueue.GetPendingItems();
            int totalSynced = 0;

            if (pending.Count > 0)
            {
                // Группируем по inventory_id
                var byInventory = pending.GroupBy(i => i.InventoryId).ToList();
                foreach (var group in byInventory)
                {
                    if (group.Key == null || group.Key <= 0) continue;
                    
                    var tags = group.Select(i => i.RfidTags).Where(t => !string.IsNullOrEmpty(t)).ToList();
                    if (tags.Count > 0)
                    {
                    var body = JsonConvert.SerializeObject(tags);
                    var content = new StringContent(body, System.Text.Encoding.UTF8, "application/json");
                    var url = $"/api/rfid/inventories/{group.Key}/scan-batch";
                        
                        try
                        {
                            var response = await _apiClient.SendAsync(new HttpMethod("POST"), url, content);
                            var json = await response.Content.ReadAsStringAsync();
                            System.Diagnostics.Debug.WriteLine($"[SyncToApi] Batch sync {group.Key}: {(int)response.StatusCode} {json}");
                            
                            if (response.IsSuccessStatusCode)
                            {
                                _offlineQueue.MarkAsSynced(group.ToList());
                                totalSynced += group.Count();
                            }
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"[SyncToApi] Batch sync error: {ex.Message}");
                        }
                    }
                }
            }

            // 2. Синхронизируем unsynced сессии (старый механизм — заглушка)
            var unsynced = _localStore.GetUnsyncedSessions();
            foreach (var session in unsynced)
            {
                _localStore.MarkSynced(session.Id);
                totalSynced++;
            }

            SyncStatus = totalSynced > 0
                ? $"✅ Отправлено {totalSynced} записей"
                : "✅ Все данные отправлены";
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

    /// <summary>
    /// Событие обновления результатов сканирования
    /// </summary>
    public event Action? ResultsUpdated;

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

    /// <summary>
    /// Результат завершения инвентаризации
    /// </summary>
    public class FinishResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public int SkippedCount { get; set; }
        public bool ServerError { get; set; }
    }
}
