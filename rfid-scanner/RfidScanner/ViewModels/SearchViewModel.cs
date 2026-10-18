using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.ViewModels;

/// <summary>
/// ViewModel для режима "Поиск" актива
/// </summary>
public class SearchViewModel : INotifyPropertyChanged
{
    private readonly RfidApiClient _apiClient;
    private readonly AssetCacheService _assetCache;

    private string _searchQuery = "";
    private Asset? _searchResult;
    private bool _isSearching;
    private string _searchStatus = "Введите инвентарный номер или RFID-метку";

    public SearchViewModel(RfidApiClient apiClient, AssetCacheService assetCache)
    {
        _apiClient = apiClient;
        _assetCache = assetCache;
    }

    public string SearchQuery
    {
        get => _searchQuery;
        set => SetProperty(ref _searchQuery, value);
    }

    public Asset? SearchResult
    {
        get => _searchResult;
        private set => SetProperty(ref _searchResult, value);
    }

    public bool IsSearching
    {
        get => _isSearching;
        private set => SetProperty(ref _isSearching, value);
    }

    public string SearchStatus
    {
        get => _searchStatus;
        private set => SetProperty(ref _searchStatus, value);
    }

    public ICommand SearchCommand => new RelayCommand(async () => await PerformSearch());

    private async Task PerformSearch()
    {
        if (string.IsNullOrWhiteSpace(SearchQuery))
        {
            SearchStatus = "Введите поисковый запрос";
            return;
        }

        IsSearching = true;
        SearchStatus = "Поиск...";

        try
        {
            // Сначала ищем в локальном кэше
            var cached = _assetCache.CheckLocalCache(SearchQuery);
            if (cached.Found)
            {
                SearchStatus = "✅ Найден в локальном кэше";
                SearchResult = new Asset
                {
                    InventoryNumber = cached.InventoryNumber,
                    Name = cached.AssetName,
                    RfidTag = SearchQuery
                };
                return;
            }

            // Ищем по API
            var asset = await _apiClient.GetAssetByRfidAsync(SearchQuery);
            if (asset != null)
            {
                SearchStatus = "✅ Найден в базе";
                SearchResult = asset;
            }
            else
            {
                SearchStatus = "❌ Не найден";
                SearchResult = null;
            }
        }
        catch (Exception ex)
        {
            SearchStatus = $"Ошибка: {ex.Message}";
            SearchResult = null;
        }
        finally
        {
            IsSearching = false;
        }
    }

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
