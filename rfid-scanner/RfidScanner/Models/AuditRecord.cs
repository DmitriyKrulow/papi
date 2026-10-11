namespace RfidScanner.Models;

/// <summary>
/// Тип операции аудита
/// </summary>
public enum AuditAction
{
    SessionStart,      // Начало сессии
    SessionPause,      // Пауза
    SessionResume,     // Возобновление
    SessionFinish,     // Завершение
    TagMatched,        // Тег найден
    TagExtra,          // Лишний тег
    TagSkipped,        // Пропущен
    CacheLoad,         // Загрузка кэша
    SyncComplete       // Синхронизация
}

/// <summary>
/// Запись аудита (кто, когда, что)
/// </summary>
public class AuditRecord
{
    public long Id { get; set; }
    public AuditAction Action { get; set; }
    public string? Username { get; set; }
    public string? SessionId { get; set; }
    public string? RoomName { get; set; }
    public string? Details { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
