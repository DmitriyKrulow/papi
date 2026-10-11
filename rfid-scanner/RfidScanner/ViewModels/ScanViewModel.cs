using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для страницы сканирования
/// </summary>
public class ScanViewModel : BaseViewModel
{
    private readonly RfidApiClient _apiClient;
    private readonly OfflineQueueService _offlineQueue;
    private readonly ConfigService _config;

    private string _rfidBuffer = string.Empty;
    private string _lastScannedTag = string.Empty;
    private ObservableCollection<ScanResult> _recentScans = new();
    private ScanResult? _lastResult;
    private bool _isScanning;

    public ScanViewModel(RfidApiClient apiClient, OfflineQueueService offlineQueue, ConfigService config)
    {
        _apiClient = apiClient;
        _offlineQueue = offlineQueue;
        _config = config;
    }

    public string RfidBuffer
    {
        get => _rfidBuffer;
        set => SetProperty(ref _rfidBuffer, value);
    }

    public string LastScannedTag
    {
        get => _lastScannedTag;
        set => SetProperty(ref _lastScannedTag, value);
    }

    public ObservableCollection<ScanResult> RecentScans => _recentScans;

    public ScanResult? LastResult
    {
        get => _lastResult;
        set => SetProperty(ref _lastResult, value);
    }

    public bool IsScanning
    {
        get => _isScanning;
        set => SetProperty(ref _isScanning, value);
    }

    public ICommand ClearBufferCommand => new RelayCommand(ClearBuffer);
    public ICommand ProcessTagCommand => new RelayCommand(ProcessCurrentTag);

    /// <summary>
    /// Добавить символ в буфер (от HID-сканера)
    /// </summary>
    public void AddChar(char c)
    {
        if (c == '\r' || c == '\n')
        {
            ProcessCurrentTag();
        }
        else
        {
            RfidBuffer += c;
        }
    }

    public async void ProcessCurrentTag()
    {
        if (string.IsNullOrWhiteSpace(RfidBuffer))
            return;

        var tag = RfidBuffer.Trim();
        RfidBuffer = string.Empty;
        LastScannedTag = tag;
        IsScanning = true;

        try
        {
            // Пытаемся определить контекст (инвентаризация или помещение)
            // Для простоты — ищем актив по RFID
            var asset = await _apiClient.GetAssetByRfidAsync(tag);
            
            if (asset != null)
            {
                LastResult = new ScanResult
                {
                    Success = true,
                    Message = $"Найден: {asset.Name} (инв. {asset.InventoryNumber})",
                    RfidTag = tag,
                    AssetId = asset.Id,
                    InventoryNumber = asset.InventoryNumber,
                    AssetName = asset.Name,
                    Location = asset.Location
                };
            }
            else
            {
                LastResult = new ScanResult
                {
                    Success = false,
                    Message = $"Актив с меткой '{tag}' не найден",
                    RfidTag = tag
                };

                // Сохраняем в офлайн-очередь
                _offlineQueue.AddItem(new OfflineQueueItem
                {
                    OperationType = Models.OfflineOperationType.Scan,
                    RfidTags = tag
                });
            }

            // Добавляем в последние сканирования
            _recentScans.Insert(0, LastResult);
            if (_recentScans.Count > 50)
                _recentScans.RemoveAt(50);
        }
        catch (Exception ex)
        {
            LastResult = new ScanResult
            {
                Success = false,
                Message = $"Ошибка: {ex.Message}",
                RfidTag = tag
            };
        }
        finally
        {
            IsScanning = false;
        }
    }

    private void ClearBuffer()
    {
        RfidBuffer = string.Empty;
    }
}
