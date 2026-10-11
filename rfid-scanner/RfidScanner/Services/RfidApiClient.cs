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

    // ==================== Аутентификация ====================

    public async Task<bool> AuthenticateAsync()
    {
        try
        {
            var result = await GetJsonAsync<Dictionary<string, object>>("/api/rfid/auth/verify");
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
        var result = await GetJsonAsync<Dictionary<string, object>>("/api/rfid/inventories");
        if (result == null || !result.ContainsKey("inventories"))
            return new();

        var json = JsonConvert.SerializeObject(result["inventories"]);
        return JsonConvert.DeserializeObject<List<Inventory>>(json) ?? new();
    }

    public async Task<List<InventoryItem>> GetInventoryAssetsAsync(int inventoryId)
    {
        var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/inventories/{inventoryId}/assets");
        if (result == null || !result.ContainsKey("assets"))
            return new();

        var json = JsonConvert.SerializeObject(result["assets"]);
        return JsonConvert.DeserializeObject<List<InventoryItem>>(json) ?? new();
    }

    public async Task<double> GetInventoryProgressAsync(int inventoryId)
    {
        var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/inventories/{inventoryId}/status");
        if (result == null || !result.ContainsKey("progress_percent"))
            return 0;

        return Convert.ToDouble(result["progress_percent"]);
    }

    // ==================== Помещения ====================

    public async Task<List<Room>> GetRoomsAsync()
    {
        var result = await GetJsonAsync<Dictionary<string, object>>("/api/rfid/rooms");
        if (result == null || !result.ContainsKey("rooms"))
            return new();

        var json = JsonConvert.SerializeObject(result["rooms"]);
        return JsonConvert.DeserializeObject<List<Room>>(json) ?? new();
    }

    // ==================== Поиск актива ====================

    public async Task<List<Asset>> GetRoomAssetsAsync(int roomId)
    {
        var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/rooms/{roomId}/assets");
        if (result == null || !result.ContainsKey("assets"))
            return new();

        var json = JsonConvert.SerializeObject(result["assets"]);
        return JsonConvert.DeserializeObject<List<Asset>>(json) ?? new();
    }

    // ==================== Инвентаризации ====================

    public async Task<Dictionary<string, object>> CreateInventoryAsync(int roomId, string roomName)
    {
        var url = $"/api/rfid/inventories?room_id={roomId}&room_name={Uri.EscapeDataString(roomName)}";
        var response = await SendAsync(HttpMethod.Post, url);
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<Dictionary<string, object>>(json) ?? new();
    }

    public async Task<Asset?> GetAssetByRfidAsync(string rfidTag)
    {
        var result = await GetJsonAsync<Dictionary<string, object>>($"/api/rfid/assets/by-rfid/{Uri.EscapeDataString(rfidTag)}");
        if (result == null || !(result.ContainsKey("found") && (bool)result["found"]!))
            return null;

        if (result.ContainsKey("asset"))
        {
            var json = JsonConvert.SerializeObject(result["asset"]);
            return JsonConvert.DeserializeObject<Asset>(json);
        }
        return null;
    }

    // ==================== Сканирование ====================

    public async Task<ScanResult> ScanAsync(int inventoryId, string rfidTag)
    {
        var result = await PostJsonAsync<Dictionary<string, object>>(
            $"/api/rfid/inventories/{inventoryId}/scan?rfid_tag={Uri.EscapeDataString(rfidTag)}");

        if (result == null)
            return new() { Success = false, Message = "Ошибка ответа сервера" };

        return new ScanResult
        {
            Success = (bool)result["success"],
            Message = result["message"]?.ToString() ?? "",
            RfidTag = rfidTag,
            InventoryId = inventoryId,
            AssetId = result["asset_id"] != null ? Convert.ToInt32(result["asset_id"]) : null,
            InventoryNumber = result["inventory_number"]?.ToString(),
            AssetName = result["asset_name"]?.ToString(),
            Location = result["location"]?.ToString(),
            Responsible = result["responsible"]?.ToString(),
            FoundCount = result["found_count"] != null ? Convert.ToInt32(result["found_count"]) : null,
            MissingCount = result["missing_count"] != null ? Convert.ToInt32(result["missing_count"]) : null,
            Remaining = result["remaining"] != null ? Convert.ToInt32(result["remaining"]) : null,
        };
    }

    public async Task<BatchScanResult> ScanBatchAsync(int inventoryId, List<string> rfidTags)
    {
        var body = JsonConvert.SerializeObject(new { rfid_tags = rfidTags });
        var result = await PostJsonAsync<Dictionary<string, object>>(
            $"/api/rfid/inventories/{inventoryId}/scan-batch", body);

        if (result == null)
            return new() { Success = false };

        var details = result["details"] as Dictionary<string, object>;
        var foundJson = JsonConvert.SerializeObject(details?["found"]);
        var notFoundJson = JsonConvert.SerializeObject(details?["not_found"]);

        return new BatchScanResult
        {
            Success = (bool)result["success"],
            InventoryId = Convert.ToInt32(result["inventory_id"]),
            TotalScanned = Convert.ToInt32(result["total_scanned"]),
            Found = Convert.ToInt32(result["found"]),
            NotFound = Convert.ToInt32(result["not_found"]),
            AlreadyConfirmed = Convert.ToInt32(result["already_confirmed"]),
            FoundItems = JsonConvert.DeserializeObject<List<FoundItem>>(foundJson) ?? new(),
            NotFoundItems = JsonConvert.DeserializeObject<List<NotFoundItem>>(notFoundJson) ?? new(),
        };
    }

    // ==================== Пассивное сканирование помещения ====================

    public async Task<Dictionary<string, object>> ScanRoomAsync(int roomId, List<string> rfidTags)
    {
        var body = JsonConvert.SerializeObject(new { room_id = roomId, rfid_tags = rfidTags });
        return await PostJsonAsync<Dictionary<string, object>>("/api/rfid/scan-room", body)
            ?? new();
    }

    // ==================== Приёмка ====================

    public async Task<Dictionary<string, object>> ReceiveAsync(
        string departmentCode, string responsiblePerson, List<string> rfidTags, string? docNumber = null)
    {
        var body = JsonConvert.SerializeObject(new
        {
            department_code = departmentCode,
            responsible_person = responsiblePerson,
            rfid_tags = rfidTags,
            document_number = docNumber
        });
        return await PostJsonAsync<Dictionary<string, object>>("/api/rfid/receive", body) ?? new();
    }

    // ==================== Перемещение ====================

    public async Task<Dictionary<string, object>> MoveAsync(
        int fromRoomId, int toRoomId, List<string> rfidTags, string? reason = null, string? docNumber = null)
    {
        var body = JsonConvert.SerializeObject(new
        {
            from_room_id = fromRoomId,
            to_room_id = toRoomId,
            rfid_tags = rfidTags,
            reason = reason,
            document_number = docNumber
        });
        return await PostJsonAsync<Dictionary<string, object>>("/api/rfid/move", body) ?? new();
    }

    public void Dispose()
    {
        _httpClient?.Dispose();
    }
}
