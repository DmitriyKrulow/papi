namespace RfidScanner.Models;

/// <summary>
/// Модель инвентаризации
/// </summary>
public class Inventory
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public DateTime? CheckDate { get; set; }
    public string CheckType { get; set; } = string.Empty;
    public string ScopeName { get; set; } = string.Empty;
    public string Department { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int TotalChecked { get; set; }
    public int Found { get; set; }
    public int Missing { get; set; }
    public string Creator { get; set; } = string.Empty;
    public string Responsible { get; set; } = string.Empty;
    public DateTime? StartedAt { get; set; }

    // Вычисляемые свойства
    public int Pending => TotalChecked - Found - Missing;
    public double ProgressPercent => TotalChecked > 0 
        ? Math.Round((Found + Missing) * 100.0 / TotalChecked, 1) 
        : 0;
}
