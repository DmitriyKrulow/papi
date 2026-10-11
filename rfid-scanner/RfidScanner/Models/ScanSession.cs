namespace RfidScanner.Models;

/// <summary>
/// Статус сканирования актива
/// </summary>
public enum ScanAssetStatus
{
    Matched,        // ✅ Совпало с API
    Extra,          // ⚠️ Лишний (нет в API)
    Missing,        // ❌ Не найден
    Error           // ⛔ Ошибка
}

/// <summary>
/// Результат сканирования одного тега
/// </summary>
public class ScanResultItem
{
    public string RfidTag { get; set; } = string.Empty;
    public ScanAssetStatus Status { get; set; } = ScanAssetStatus.Missing;
    public string? AssetName { get; set; }
    public string? InventoryNumber { get; set; }
    public int? RoomId { get; set; }
    public DateTime ScannedAt { get; set; } = DateTime.Now;
    public bool ManuallyConfirmed { get; set; }
    public string? Note { get; set; }
}

/// <summary>
/// Сессия сканирования (пауза/сброс/возобновление)
/// </summary>
public class ScanSession
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string RoomName { get; set; } = string.Empty;
    public int RoomId { get; set; }
    public int InventoryId { get; set; }
    public DateTime StartedAt { get; set; } = DateTime.Now;
    public DateTime? PausedAt { get; set; }
    public DateTime? FinishedAt { get; set; }
    public SessionState State { get; set; } = SessionState.Active;

    // Результаты
    public List<ScanResultItem> Results { get; set; } = new();
    public HashSet<string> SeenTags { get; set; } = new();

    // Статистика
    public int TotalScanned => Results.Count;
    public int MatchedCount => Results.Count(r => r.Status == ScanAssetStatus.Matched);
    public int ExtraCount => Results.Count(r => r.Status == ScanAssetStatus.Extra);
    public int MissingCount => Results.Count(r => r.Status == ScanAssetStatus.Missing);
    public int ErrorCount => Results.Count(r => r.Status == ScanAssetStatus.Error);

    // Управление
    public bool IsPaused => State == SessionState.Paused;
    public bool IsFinished => State == SessionState.Finished;

    public void Pause() => State = SessionState.Paused;
    public void Resume() => State = SessionState.Active;
    public void Finish() => State = SessionState.Finished;
    public void Reset()
    {
        Results.Clear();
        SeenTags.Clear();
        State = SessionState.Active;
        StartedAt = DateTime.Now;
        PausedAt = null;
        FinishedAt = null;
    }
}

public enum SessionState
{
    Active,
    Paused,
    Finished
}
