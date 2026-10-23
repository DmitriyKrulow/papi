using Newtonsoft.Json;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace RfidScanner.Models;

/// <summary>
/// Модель помещения
/// </summary>
public class Room : INotifyPropertyChanged
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
    
    /// <summary>Выделена ли комната</summary>
    public bool Selected
    {
        get => _selected;
        set
        {
            if (_selected == value) return;
            _selected = value;
            OnPropertyChanged();
        }
    }
    private bool _selected;
    
    public void ClearSelection() => Selected = false;
    
    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
