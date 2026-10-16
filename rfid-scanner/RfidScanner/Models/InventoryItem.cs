using Newtonsoft.Json;

namespace RfidScanner.Models;

/// <summary>
/// Актив в контексте инвентаризации
/// </summary>
public class InventoryItem
{
    [JsonProperty("asset_id")]
    public int AssetId { get; set; }

    [JsonProperty("inventory_number")]
    public string InventoryNumber { get; set; } = string.Empty;

    [JsonProperty("name")]
    public string Name { get; set; } = string.Empty;

    [JsonProperty("model")]
    public string Model { get; set; } = string.Empty;

    [JsonProperty("location")]
    public string Location { get; set; } = string.Empty;

    [JsonProperty("responsible")]
    public string Responsible { get; set; } = string.Empty;

    [JsonProperty("department")]
    public string Department { get; set; } = string.Empty;

    [JsonProperty("rfid_tag")]
    public string RfidTag { get; set; } = string.Empty;

    [JsonProperty("check_status")]
    public string CheckStatus { get; set; } = "pending"; // pending, found, missing

    [JsonProperty("confirmed_by")]
    public string? ConfirmedBy { get; set; }

    [JsonProperty("confirmed_at")]
    public DateTime? ConfirmedAt { get; set; }
}
