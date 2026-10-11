using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using RfidScanner.Models;

namespace RfidScanner.Services;

/// <summary>
/// HTTP-клиент для RFID API
/// </summary>
public class RfidApiClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;
    private readonly string _apiKey;

    public RfidApiClient(string baseUrl, string apiKey)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _apiKey = apiKey;
        _httpClient = new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(30);
    }

    private async Task<HttpResponseMessage> SendAsync(HttpMethod method, string url, StringContent? content = null)
    {
        var fullUrl = $"{_baseUrl}{url}";
        var request = new HttpRequestMessage(method, fullUrl);
        request.Headers.Add("X-API-Key", _apiKey);
        if (content != null)
            request.Content = content;
        
        return await _httpClient.SendAsync(request);
    }

    private async Task<T?> GetJsonAsync<T>(string endpoint)
    {
        var response = await SendAsync(HttpMethod.Get, endpoint);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<T>(json);
    }

    private async Task<T?> PostJsonAsync<T>(string endpoint, string? body = null)
    {
        var content = body != null ? new StringContent(body, Encoding.UTF8, "application/json") : null;
        var response = await SendAsync(HttpMethod.Post, endpoint, content);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<T>(json);
    }

    public async Task<bool> AuthenticateAsync()
    {
        try
        {
            var result = await PostJsonAsync<Dictionary<string, object>>("/api/rfid/auth/verify");
            return result != null && result.ContainsKey("authenticated");
        }
        catch
        {
            return false;
        }
    }

    // ==================== Инвентаризации ====================

    public async Task<List<Inventory>> GetActiveInventoriesAsync()
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>("/api/rfid/inventories");
            if (result == null || !result.ContainsKey("inventories"))
                return new();

            var json = JsonConvert.SerializeObject(result["inventories"]);
            return JsonConvert.DeserializeObject<List<Inventory>>(json) ?? new();
        }
        catch
        {
            return new();
        }
    }

    public async Task<List<InventoryItem>> GetInventoryAssetsAsync(int inventoryId)
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/inventories/{inventoryId}");
            if (result == null || !result.ContainsKey("items"))
                return new();

            var json = JsonConvert.SerializeObject(result["items"]);
            return JsonConvert.DeserializeObject<List<InventoryItem>>(json) ?? new();
        }
        catch
        {
            return new();
        }
    }

    public async Task<double> GetInventoryProgressAsync(int inventoryId)
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/inventories/{inventoryId}/status");
            if (result == null || !result.ContainsKey("progress_percent"))
                return 0;

            return Convert.ToDouble(result["progress_percent"]);
        }
        catch
        {
            return 0;
        }
    }

    public async Task<Dictionary<string, object>> CreateInventoryAsync(int roomId, string roomName)
    {
        var url = $"/api/rfid/inventories?room_id={roomId}&room_name={Uri.EscapeDataString(roomName)}";
        var response = await SendAsync(HttpMethod.Post, url);
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<Dictionary<string, object>>(json) ?? new();
    }

    // ==================== Помещения ====================

    public async Task<List<Room>> GetRoomsAsync()
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>("/api/rfid/rooms");
            if (result == null || !result.ContainsKey("rooms"))
                return new();

            var json = JsonConvert.SerializeObject(result["rooms"]);
            return JsonConvert.DeserializeObject<List<Room>>(json) ?? new();
        }
        catch
        {
            return new();
        }
    }

    // ==================== Поиск актива ====================

    public async Task<List<Asset>> GetRoomAssetsAsync(int roomId)
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/rooms/{roomId}/assets");
            if (result == null || !result.ContainsKey("assets"))
                return new();

            var json = JsonConvert.SerializeObject(result["assets"]);
            return JsonConvert.DeserializeObject<List<Asset>>(json) ?? new();
        }
        catch
        {
            return new();
        }
    }

    public async Task<Asset?> GetAssetByRfidAsync(string rfidTag)
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/assets/by-rfid/{Uri.EscapeDataString(rfidTag)}");
            if (result == null || !result.ContainsKey("asset"))
                return null;

            var json = JsonConvert.SerializeObject(result["asset"]);
            return JsonConvert.DeserializeObject<Asset>(json);
        }
        catch
        {
            return null;
        }
    }

    // ==================== Сканер ====================

    public async Task<ScanResult> ScanAsync(int inventoryId, string rfidTag)
    {
        try
        {
            var body = JsonConvert.SerializeObject(new { rfid_tag = rfidTag });
            var content = new StringContent(body, Encoding.UTF8, "application/json");
            var response = await SendAsync(HttpMethod.Post, $"/api/rfid/inventories/{inventoryId}/scan", content);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            var result = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            return new ScanResult { Success = result != null && result.ContainsKey("success") && result["success"].ToString() == "True" };
        }
        catch
        {
            return new ScanResult { Success = false };
        }
    }

    public class ScanResult
    {
        public bool Success { get; set; }
    }

    public async Task<bool> AuthenticateAsync(string apiKey)
    {
        var client = new HttpClient();
        client.Timeout = TimeSpan.FromSeconds(10);
        try
        {
            var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/api/rfid/auth/verify");
            request.Headers.Add("X-API-Key", apiKey);
            var response = await client.SendAsync(request);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
        finally
        {
            client.Dispose();
        }
    }
}
