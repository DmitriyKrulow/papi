namespace RfidScanner.Models;

/// <summary>
/// Тип операции для офлайн-очереди
/// </summary>
public enum OfflineOperationType
{
    Scan,           // Одиночное сканирование
    BatchScan,      // Пакетное сканирование
    RoomScan,       // Пассивное сканирование помещения
    Receive,        // Приёмка
    Move            // Перемещение
}

/// <summary>
/// Офлайн-операция в очереди синхронизации
/// </summary>
public class OfflineQueueItem
{
    public long Id { get; set; }
    public OfflineOperationType OperationType { get; set; }
    public string RfidTags { get; set; } = string.Empty; // JSON array
    public int? InventoryId { get; set; }
    public int? RoomId { get; set; }
    public string? DepartmentCode { get; set; }
    public string? ResponsiblePerson { get; set; }
    public string? FromRoomId { get; set; }
    public string? ToRoomId { get; set; }
    public string? Reason { get; set; }
    public string? DocumentNumber { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? SyncedAt { get; set; }
    public bool IsSynced { get; set; }
    public string? ErrorMessage { get; set; }
}
