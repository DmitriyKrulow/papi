namespace RfidScanner.Models;

/// <summary>
/// Модель актива из API
/// </summary>
public class Asset
{
    public int Id { get; set; }
    public string? InventoryNumber { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Model { get; set; }
    public string? AssetType { get; set; }
    public string Status { get; set; } = "active";
    public string? Location { get; set; }
    public string? Room { get; set; }
    public string? Responsible { get; set; }
    public string? Employee { get; set; }
    public string? Department { get; set; }
    public string? SerialNumber { get; set; }
    public string? RfidTag { get; set; }
    public DateTime? PurchaseDate { get; set; }
    public decimal? PurchasePrice { get; set; }
    public decimal? CurrentValue { get; set; }
}
