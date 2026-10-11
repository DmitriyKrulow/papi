using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// Интеграция с внешними системами (1С, CMMS)
/// </summary>
public class ExternalIntegrationService
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;
    private readonly string _apiKey;

    public ExternalIntegrationService(string baseUrl, string apiKey)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _apiKey = apiKey;
        _httpClient = new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(60);
    }

    // ==================== 1С ====================

    /// <summary>
    /// Синхронизация активов с 1С
    /// </summary>
    public async Task<bool> SyncWith1CAsync(List<Asset> assets, string syncDirection = "push")
    {
        try
        {
            var body = JsonConvert.SerializeObject(new
            {
                direction = syncDirection,
                assets = assets.Select(a => new
                {
                    a.InventoryNumber,
                    a.Name,
                    a.RfidTag,
                    a.SerialNumber,
                    a.Department,
                    a.Responsible,
                    a.Location
                }),
                timestamp = DateTime.Now.ToString("o")
            });

            var content = new StringContent(body, Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync($"{_baseUrl}/api/integration/1c/sync", content);
            
            response.EnsureSuccessStatusCode();
            return true;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Запросить обновления из 1С
    /// </summary>
    public async Task<List<Asset>> FetchFrom1CAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/api/integration/1c/fetch");
            response.EnsureSuccessStatusCode();
            
            var json = await response.Content.ReadAsStringAsync();
            var result = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            
            if (result != null && result.ContainsKey("assets"))
            {
                var assetsJson = JsonConvert.SerializeObject(result["assets"]);
                return JsonConvert.DeserializeObject<List<Asset>>(assetsJson) ?? new();
            }
            
            return new();
        }
        catch
        {
            return new();
        }
    }

    /// <summary>
    /// Проверить подключение к 1С
    /// </summary>
    public async Task<bool> TestConnection1CAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/api/integration/1c/status");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    // ==================== CMMS ====================

    /// <summary>
    /// Отправить результат инвентаризации в CMMS
    /// </summary>
    public async Task<bool> SendToCMMSAsync(int inventoryId, List<ScanResultItem> results)
    {
        try
        {
            var body = JsonConvert.SerializeObject(new
            {
                inventory_id = inventoryId,
                results = results.Select(r => new
                {
                    r.RfidTag,
                    status = r.Status.ToString(),
                    r.AssetName,
                    r.InventoryNumber,
                    r.Note
                }),
                timestamp = DateTime.Now.ToString("o")
            });

            var content = new StringContent(body, Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync($"{_baseUrl}/api/integration/cmms/inventory", content);
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Получить активы из CMMS
    /// </summary>
    public async Task<List<Asset>> FetchFromCMMSAsync(int departmentId)
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/api/integration/cmms/assets?dept_id={departmentId}");
            response.EnsureSuccessStatusCode();
            
            var json = await response.Content.ReadAsStringAsync();
            var result = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            
            if (result != null && result.ContainsKey("assets"))
            {
                var assetsJson = JsonConvert.SerializeObject(result["assets"]);
                return JsonConvert.DeserializeObject<List<Asset>>(assetsJson) ?? new();
            }
            
            return new();
        }
        catch
        {
            return new();
        }
    }

    public void Dispose()
    {
        _httpClient?.Dispose();
    }
}
