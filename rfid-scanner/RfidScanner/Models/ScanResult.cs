namespace RfidScanner.Models;

/// <summary>
/// Результат одиночного сканирования
/// </summary>
public class ScanResult
{
    public bool Success { get; set; }
    public string Message { get; set; } = string.Empty;
    public string RfidTag { get; set; } = string.Empty;
    public int? InventoryId { get; set; }
    public int? AssetId { get; set; }
    public string? InventoryNumber { get; set; }
    public string? AssetName { get; set; }
    public string? Location { get; set; }
    public string? Responsible { get; set; }
    public int? FoundCount { get; set; }
    public int? MissingCount { get; set; }
    public int? Remaining { get; set; }
}

/// <summary>
/// Результат пакетного сканирования
/// </summary>
public class BatchScanResult
{
    public bool Success { get; set; }
    public int InventoryId { get; set; }
    public int TotalScanned { get; set; }
    public int Found { get; set; }
    public int NotFound { get; set; }
    public int AlreadyConfirmed { get; set; }
    public List<FoundItem> FoundItems { get; set; } = new();
    public List<NotFoundItem> NotFoundItems { get; set; } = new();
}

public class FoundItem
{
    public string RfidTag { get; set; } = string.Empty;
    public int AssetId { get; set; }
    public string InventoryNumber { get; set; } = string.Empty;
    public string AssetName { get; set; } = string.Empty;
}

public class NotFoundItem
{
    public string RfidTag { get; set; } = string.Empty;
    public int? AssetId { get; set; }
    public string Message { get; set; } = string.Empty;
}
