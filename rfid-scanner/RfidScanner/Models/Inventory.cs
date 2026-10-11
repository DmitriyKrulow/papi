using Newtonsoft.Json;

namespace RfidScanner.Models;

/// <summary>
/// Модель инвентаризации
/// </summary>
public class Inventory
{
    public int Id { get; set; }
    
    [JsonProperty("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonProperty("check_date")]
    public DateTime? CheckDate { get; set; }
    
    [JsonProperty("check_type")]
    public string CheckType { get; set; } = string.Empty;
    
    [JsonProperty("scope_name")]
    public string ScopeName { get; set; } = string.Empty;
    
    [JsonProperty("department")]
    public string Department { get; set; } = string.Empty;
    
    [JsonProperty("status")]
    public string Status { get; set; } = string.Empty;
    
    [JsonProperty("total_checked")]
    public int TotalChecked { get; set; }
    
    [JsonProperty("found")]
    public int Found { get; set; }
    
    [JsonProperty("missing")]
    public int Missing { get; set; }
    
    [JsonProperty("creator")]
    public string Creator { get; set; } = string.Empty;
    
    [JsonProperty("responsible")]
    public string Responsible { get; set; } = string.Empty;
    
    [JsonProperty("started_at")]
    public DateTime? StartedAt { get; set; }

    // Вычисляемые свойства
    public int Pending => TotalChecked - Found - Missing;
    public double ProgressPercent => TotalChecked > 0 
        ? Math.Round((Found + Missing) * 100.0 / TotalChecked, 1) 
        : 0;
    public string ProgressPercentText => TotalChecked > 0 
        ? $"{Math.Round((Found + Missing) * 100.0 / TotalChecked, 1)}%" 
        : "0%";
}
