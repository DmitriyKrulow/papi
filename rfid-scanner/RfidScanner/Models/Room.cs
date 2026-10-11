using Newtonsoft.Json;

namespace RfidScanner.Models;

/// <summary>
/// Модель помещения
/// </summary>
public class Room
{
    [JsonProperty("id")]
    public int Id { get; set; }
    
    [JsonProperty("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonProperty("building")]
    public string? Building { get; set; }
    
    [JsonProperty("floor")]
    public string? Floor { get; set; }
    
    [JsonProperty("department")]
    public string? Department { get; set; }
    
    [JsonProperty("department_id")]
    public int? DepartmentId { get; set; }
}
