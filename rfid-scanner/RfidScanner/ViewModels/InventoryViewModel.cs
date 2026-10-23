using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для страницы инвентаризации
/// </summary>
public class InventoryViewModel : BaseViewModel
{
    private readonly RfidApiClient _apiClient;
    private readonly OfflineQueueService _offlineQueue;

    private Inventory? _selectedInventory;
    private ObservableCollection<InventoryItem> _items = new();
    private string _searchText = string.Empty;
    private bool _isLoading;

    public InventoryViewModel(RfidApiClient apiClient, OfflineQueueService offlineQueue)
    {
        _apiClient = apiClient;
        _offlineQueue = offlineQueue;
    }

    public Inventory? SelectedInventory
    {
        get => _selectedInventory;
        set => SetProperty(ref _selectedInventory, value);
    }

    public ObservableCollection<InventoryItem> Items => _items;

    public string SearchText
    {
        get => _searchText;
        set
        {
            if (SetProperty(ref _searchText, value))
                FilterItems();
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        set => SetProperty(ref _isLoading, value);
    }

    public int PendingCount => _items.Count(i => i.CheckStatus == "pending");
    public int FoundCount => _items.Count(i => i.CheckStatus == "found");
    public int MissingCount => _items.Count(i => i.CheckStatus == "missing");

    public ICommand LoadInventoryCommand => new RelayCommand<int>(async id => await LoadInventory(id));
    public ICommand ScanCommand => new RelayCommand<string>(async tag => await ScanTag(tag ?? string.Empty));

    private async Task LoadInventory(int inventoryId)
    {
        IsLoading = true;
        try
        {
            var items = await _apiClient.GetInventoryAssetsAsync(inventoryId);
            _items.Clear();
            foreach (var item in items)
                _items.Add(item);
        }
        catch (Exception ex)
        {
            // Показать ошибку
            System.Diagnostics.Debug.WriteLine($"[LoadInventory] Error: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async Task ScanTag(string rfidTag)
    {
        if (SelectedInventory == null)
            return;

        try
        {
            var result = await _apiClient.ScanAsync(SelectedInventory.Id, rfidTag);
            if (result.Success)
            {
                // Обновить статус элемента — бэкенд возвращает asset_id
                // Ищем элемент по asset_id, а не по rfid_tag (надёжнее)
                var item = _items.FirstOrDefault(i => !string.IsNullOrEmpty(i.RfidTag) 
                    && i.RfidTag.Trim().ToUpper() == rfidTag.Trim().ToUpper());
                if (item != null)
                {
                    item.CheckStatus = "found";
                }
                else
                {
                    // Если не нашли по RFID — пробуем обновить через API
                    // Получаем обновлённый список активов
                    await LoadInventory(SelectedInventory.Id);
                }
            }
            else
            {
                // Добавить в очередь если офлайн
                _offlineQueue.AddItem(new OfflineQueueItem
                {
                    OperationType = Models.OfflineOperationType.Scan,
                    RfidTags = rfidTag,
                    InventoryId = SelectedInventory.Id
                });
            }
        }
        catch
        {
            // Офлайн-режим
        }
    }

    private void FilterItems()
    {
        // Реализовать фильтрацию
    }
}
