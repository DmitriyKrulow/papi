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

    /// <summary>
    /// JWT-токен авторизованного пользователя (для Authorization: Bearer)
    /// </summary>
    public static string? UserToken { get; set; }

    public RfidApiClient(string baseUrl, string apiKey)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _apiKey = apiKey;
        _httpClient = new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(30);
    }

    public async Task<HttpResponseMessage> SendAsync(HttpMethod method, string url, StringContent? content = null)
    {
        var fullUrl = $"{_baseUrl}{url}";
        var request = new HttpRequestMessage(method, fullUrl);
        request.Headers.Add("X-API-Key", _apiKey);
        if (UserToken != null)
            request.Headers.Add("Authorization", $"Bearer {UserToken}");
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
        try
        {
            var url = $"/api/rfid/inventories?room_id={roomId}&room_name={Uri.EscapeDataString(roomName)}";
            var response = await SendAsync(HttpMethod.Post, url);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] CreateInventory response: {(int)response.StatusCode} {json}");

            if (!response.IsSuccessStatusCode)
            {
                string detail = json;
                try
                {
                    var errObj = Newtonsoft.Json.Linq.JObject.Parse(json);
                    detail = errObj["detail"]?.ToString() ?? json;
                }
                catch { }
                throw new InvalidOperationException($"Не удалось создать инвентаризацию: HTTP {(int)response.StatusCode} — {detail}");
            }

            return JsonConvert.DeserializeObject<Dictionary<string, object>>(json) ?? new();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] CreateInventory ERROR: {ex.Message}");
            throw;
        }
    }

    /// <summary>
    /// Пометить все pending-элементы инвентаризации как отсутствующие
    /// </summary>
    public async Task<Dictionary<string, object>> SkipAllAsync(int inventoryId)
    {
        try
        {
            var url = $"/api/rfid/inventories/{inventoryId}/skip-all";
            System.Diagnostics.Debug.WriteLine($"[API] POST {url}");
            var response = await SendAsync(HttpMethod.Post, url);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] SkipAll response: {(int)response.StatusCode} {json}");

            if (!response.IsSuccessStatusCode)
            {
                string detail = json;
                try
                {
                    var errObj = Newtonsoft.Json.Linq.JObject.Parse(json);
                    detail = errObj["detail"]?.ToString() ?? json;
                }
                catch { }
                System.Diagnostics.Debug.WriteLine($"[API] SkipAll ERROR: {(int)response.StatusCode} {detail}");
                return new Dictionary<string, object> { { "success", false }, { "message", $"HTTP {(int)response.StatusCode}: {detail}" } };
            }

            return JsonConvert.DeserializeObject<Dictionary<string, object>>(json) ?? new();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] SkipAllAsync ERROR: {ex.Message}");
            return new Dictionary<string, object> { { "success", false }, { "message", $"Ошибка соединения: {ex.Message}" } };
        }
    }

    /// <summary>
    /// Пакетная отправка результатов сканирования на сервер
    /// </summary>
    public async Task<Dictionary<string, object>> SyncResultsAsync(int inventoryId, List<Dictionary<string, string>> results)
    {
        try
        {
            var body = JsonConvert.SerializeObject(new { results = results });
            var content = new StringContent(body, Encoding.UTF8, "application/json");
            var url = $"/api/rfid/inventories/{inventoryId}/sync";
            System.Diagnostics.Debug.WriteLine($"[API] POST {url}");

            var response = await SendAsync(HttpMethod.Post, url, content);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] Sync response: {(int)response.StatusCode} {json}");

            if (!response.IsSuccessStatusCode)
            {
                string detail = json;
                try
                {
                    var errObj = Newtonsoft.Json.Linq.JObject.Parse(json);
                    detail = errObj["detail"]?.ToString() ?? json;
                }
                catch { }
                System.Diagnostics.Debug.WriteLine($"[API] Sync ERROR: {(int)response.StatusCode} {detail}");
                return new Dictionary<string, object> { { "success", false }, { "message", $"HTTP {(int)response.StatusCode}: {detail}" } };
            }

            return JsonConvert.DeserializeObject<Dictionary<string, object>>(json) ?? new();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] SyncResultsAsync ERROR: {ex.Message}");
            return new Dictionary<string, object> { { "success", false }, { "message", $"Ошибка соединения: {ex.Message}" } };
        }
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

    public async Task<ScanResult> ScanAsync(int inventoryId, string rfidTag, string result = "found")
    {
        try
        {
            var url = $"/api/rfid/inventories/{inventoryId}/scan?rfid_tag={Uri.EscapeDataString(rfidTag)}&result={result}";
            System.Diagnostics.Debug.WriteLine($"[API] POST {url}");
            var response = await SendAsync(HttpMethod.Post, url);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] Scan response: {(int)response.StatusCode} {json}");

            if (!response.IsSuccessStatusCode)
            {
                string detail = json;
                try
                {
                    var errObj = Newtonsoft.Json.Linq.JObject.Parse(json);
                    detail = errObj["detail"]?.ToString() ?? json;
                }
                catch { }
                System.Diagnostics.Debug.WriteLine($"[API] Scan ERROR: {(int)response.StatusCode} {detail}");
                return new ScanResult { Success = false, Message = $"HTTP {(int)response.StatusCode}: {detail}" };
            }
            
            var resultObj = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            bool success = resultObj != null
                           && resultObj.TryGetValue("success", out var s)
                           && (s is bool b ? b : string.Equals(s?.ToString(), "True", StringComparison.OrdinalIgnoreCase));
            
            string message = "";
            bool isSurplus = false;
            if (resultObj != null)
            {
                if (resultObj.TryGetValue("message", out var m))
                    message = m?.ToString() ?? "";
                if (resultObj.TryGetValue("is_surplus", out var sur))
                    isSurplus = sur is bool sb ? sb : string.Equals(sur?.ToString(), "True", StringComparison.OrdinalIgnoreCase);
            }
            
            return new ScanResult
            {
                Success = success,
                Message = message,
                IsSurplus = isSurplus,
            };
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] ScanAsync ERROR: {ex.Message}");
            return new ScanResult { Success = false, Message = $"Ошибка соединения: {ex.Message}" };
        }
    }

    public class ScanResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public bool IsSurplus { get; set; }
    }

    // ==================== Завершение инвентаризации ====================

    public async Task<Dictionary<string, object>> FinishInventoryAsync(int inventoryId, bool skipPending = true)
    {
        try
        {
            var url = $"/api/rfid/inventories/{inventoryId}/finish?skip_pending={(skipPending ? "true" : "false")}";
            System.Diagnostics.Debug.WriteLine($"[API] POST {url}");
            
            var response = await SendAsync(HttpMethod.Post, url);
            var json = await response.Content.ReadAsStringAsync();
            System.Diagnostics.Debug.WriteLine($"[API] Finish response: {(int)response.StatusCode} {json}");
            
            if (!response.IsSuccessStatusCode)
            {
                // Пытаемся извлечь detail из ответа FastAPI
                string detail = json;
                try
                {
                    var errObj = Newtonsoft.Json.Linq.JObject.Parse(json);
                    detail = errObj["detail"]?.ToString() ?? json;
                }
                catch { }
                return new Dictionary<string, object>
                {
                    { "success", false },
                    { "message", $"HTTP {(int)response.StatusCode}: {detail}" }
                };
            }
            
            var result = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            return result ?? new();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[API] FinishInventoryAsync ERROR: {ex.Message}");
            return new Dictionary<string, object>
            {
                { "success", false },
                { "message", $"Ошибка соединения: {ex.Message}" }
            };
        }
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

    /// <summary>
    /// Аутентификация пользователя по логину и паролю через бэкенд
    /// </summary>
    public async Task<Dictionary<string, object>?> LoginAsync(string username, string password)
    {
        try
        {
            var body = JsonConvert.SerializeObject(new { username, password });
            var content = new StringContent(body, Encoding.UTF8, "application/json");
            
            // Шаг 1: Получаем JWT токен
            var response = await SendAsync(HttpMethod.Post, "/api/auth/login", content);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }
            
            var json = await response.Content.ReadAsStringAsync();
            var tokenData = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
            if (tokenData == null || !tokenData.ContainsKey("access_token"))
            {
                return null;
            }
            
            var token = tokenData["access_token"]?.ToString();
            if (string.IsNullOrEmpty(token))
            {
                return null;
            }

            // Сохраняем токен для всех последующих запросов
            UserToken = token;
            
            // Шаг 2: Получаем данные пользователя через токен
            var userClient = new HttpClient();
            userClient.Timeout = TimeSpan.FromSeconds(10);
            try
            {
                var userRequest = new HttpRequestMessage(HttpMethod.Get, $"{_baseUrl}/api/auth/me");
                userRequest.Headers.Add("Authorization", $"Bearer {token}");
                var userResponse = await userClient.SendAsync(userRequest);
                
                if (!userResponse.IsSuccessStatusCode)
                {
                    return null;
                }
                
                var userJson = await userResponse.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<Dictionary<string, object>>(userJson);
            }
            finally
            {
                userClient.Dispose();
            }
        }
        catch
        {
            return null;
        }
    }
}
