namespace RfidScanner.Models;

/// <summary>
/// Актив в контексте инвентаризации
/// </summary>
public class InventoryItem
{
    public int AssetId { get; set; }
    public string InventoryNumber { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
    public string Responsible { get; set; } = string.Empty;
    public string Department { get; set; } = string.Empty;
    public string RfidTag { get; set; } = string.Empty;
    public string CheckStatus { get; set; } = "pending"; // pending, found, missing
    public string? ConfirmedBy { get; set; }
    public DateTime? ConfirmedAt { get; set; }
}
