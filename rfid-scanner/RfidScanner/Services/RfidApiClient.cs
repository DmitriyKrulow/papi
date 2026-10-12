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
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            throw new HttpRequestException($"HTTP {response.StatusCode}: {errorContent}");
        }
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<T>(json);
    }

    private async Task<T?> PostJsonAsync<T>(string endpoint, string? body = null)
    {
        var content = body != null ? new StringContent(body, Encoding.UTF8, "application/json") : null;
        var response = await SendAsync(HttpMethod.Post, endpoint, content);
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            throw new HttpRequestException($"HTTP {response.StatusCode}: {errorContent}");
        }
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
            var settings = new JsonSerializerSettings
            {
                NullValueHandling = NullValueHandling.Ignore
            };
            return JsonConvert.DeserializeObject<List<Inventory>>(json, settings) ?? new();
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
            var url = $"/api/rfid/inventories/{inventoryId}/assets";
            System.Diagnostics.Debug.WriteLine($"[API] GET {url}");
            
            var response = await SendAsync(HttpMethod.Get, url);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] Response: {json}");
            
            if (!response.IsSuccessStatusCode)
            {
                throw new HttpRequestException($"HTTP {response.StatusCode}: {json}");
            }
            
            var result = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            if (result == null)
            {
                System.Diagnostics.Debug.WriteLine($"[API] Response is null");
                return new();
            }

            System.Diagnostics.Debug.WriteLine($"[API] Keys: {string.Join(", ", result.Keys)}");
            
            List<InventoryItem>? assets = null;
            if (result.ContainsKey("items"))
            {
                assets = JsonConvert.DeserializeObject<List<InventoryItem>>(JsonConvert.SerializeObject(result["items"])) ?? new();
            }
            else if (result.ContainsKey("assets"))
            {
                assets = JsonConvert.DeserializeObject<List<InventoryItem>>(JsonConvert.SerializeObject(result["assets"])) ?? new();
            }
            else if (result.ContainsKey("data"))
            {
                assets = JsonConvert.DeserializeObject<List<InventoryItem>>(JsonConvert.SerializeObject(result["data"])) ?? new();
            }
            else if (result.ContainsKey("inventory_items"))
            {
                assets = JsonConvert.DeserializeObject<List<InventoryItem>>(JsonConvert.SerializeObject(result["inventory_items"])) ?? new();
            }
            
            assets ??= new();
            System.Diagnostics.Debug.WriteLine($"[API] Got {assets.Count} assets");
            return assets;
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] ERROR: {ex.GetType().Name}: {ex.Message}");
            if (ex.InnerException != null)
                System.Diagnostics.Debug.WriteLine($"[API] Inner: {ex.InnerException.Message}");
            throw;
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
            var settings = new JsonSerializerSettings
            {
                NullValueHandling = NullValueHandling.Ignore
            };
            return JsonConvert.DeserializeObject<List<Room>>(json, settings) ?? new();
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
