namespace RfidScanner.Models;

/// <summary>
/// Роли пользователей в системе
/// </summary>
public enum UserRole
{
    InventoryChecker,  // Инвентаризатор — только сканирование
    Administrator,     // Администратор — полный доступ
    Accountant,        // Бухгалтер — просмотр и отчёты
    Manager            // Менеджер — просмотр, отчёты, управление помещениями
}

/// <summary>
/// Текущий пользователь системы
/// </summary>
public class AppUser
{
    public string Username { get; set; } = string.Empty;
    public UserRole Role { get; set; } = UserRole.InventoryChecker;
    public string? Department { get; set; }
    public DateTime LastLogin { get; set; } = DateTime.Now;
    [Newtonsoft.Json.JsonProperty(PropertyName = "PasswordHash")]
    public string PasswordHash { get; set; } = string.Empty;
}

/// <summary>
/// Тип ошибки считывания RFID
/// </summary>
public enum ScanErrorType
{
    NoRead,           // Метка не считана
    Interference,     // Помехи (металл, объекты)
    Duplicate,        // Дубликат (повторное считывание)
    WeakSignal,       // Слабый сигнал
    UserCancelled,    // Пользователь отменил подтверждение
    Unknown           // Неизвестная ошибка
}

/// <summary>
/// Запись об ошибке считывания
/// </summary>
public class ScanErrorRecord
{
    public string RfidTag { get; set; } = string.Empty;
    public ScanErrorType ErrorType { get; set; } = ScanErrorType.NoRead;
    public string? Message { get; set; }
    public int RetryCount { get; set; }
    public DateTime OccurredAt { get; set; } = DateTime.Now;
    public string? ResolvedBy { get; set; } // "skipped", "manually_confirmed", "retry_success"
    public bool IsResolved { get; set; }
}

/// <summary>
/// Ручное добавление актива (без RFID-метки)
/// </summary>
public class ManualAssetEntry
{
    public string InventoryNumber { get; set; } = string.Empty;
    public string AssetName { get; set; } = string.Empty;
    public string? AssetType { get; set; }
    public string? SerialNumber { get; set; }
    public string? Responsible { get; set; }
    public string? Note { get; set; }
    public DateTime EnteredAt { get; set; } = DateTime.Now;
    public string EnteredBy { get; set; } = string.Empty;
}

/// <summary>
/// Тип экспорта отчёта
/// </summary>
public enum ReportFormat
{
    Csv,    // Excel-compatible
    Json
}

/// <summary>
/// Параметры отчёта
/// </summary>
public class ReportParameters
{
    public int RoomId { get; set; }
    public string RoomName { get; set; } = string.Empty;
    public DateTime FromDate { get; set; } = DateTime.Now.AddDays(-30);
    public DateTime ToDate { get; set; } = DateTime.Now;
    public string? Username { get; set; }
    public bool IncludeExtra { get; set; } = true;
    public bool IncludeMissing { get; set; } = true;
    public bool IncludeMatched { get; set; } = true;
}
