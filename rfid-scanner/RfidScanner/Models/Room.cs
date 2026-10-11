namespace RfidScanner.Models;

/// <summary>
/// Модель помещения
/// </summary>
public class Room
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Building { get; set; }
    public string? Floor { get; set; }
    public string? Department { get; set; }
    public int? DepartmentId { get; set; }
}
