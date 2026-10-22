using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace RfidScanner.Models;

/// <summary>
/// Отображение актива в списке помещения
/// </summary>
public class AssetDisplayItem : INotifyPropertyChanged
{
    private string _statusText = "⏳ Ожидание";
    private string _statusColor = "#FF9800"; // Orange
    private bool _isConfirmed = false;
    
    public Asset Asset { get; set; } = new();
    public bool IsChecked { get; set; }
    public int AssetId { get; set; } // ID актива для отправки на сервер
    public bool IsConfirmed
    {
        get => _isConfirmed;
        set
        {
            if (_isConfirmed == value) return;
            _isConfirmed = value;
            OnPropertyChanged();
        }
    }
    
    public string AssetName => Asset.Name ?? Asset.InventoryNumber ?? "Без названия";
    public string InventoryNumber => Asset.InventoryNumber ?? "—";
    public string RfidTag => Asset.RfidTag ?? "—";
    public string Location => Asset.Location ?? "—";
    
    public string StatusText
    {
        get => _statusText;
        set
        {
            if (_statusText == value) return;
            _statusText = value;
            OnPropertyChanged();
        }
    }
    
    public string StatusColor
    {
        get => _statusColor;
        set
        {
            if (_statusColor == value) return;
            _statusColor = value;
            OnPropertyChanged();
        }
    }

    public void MarkAsChecked()
    {
        IsChecked = true;
        StatusText = "✅ Найдено";
        StatusColor = "#4CAF50"; // Green
    }

    public void MarkAsPending()
    {
        IsChecked = false;
        StatusText = "⏳ Ожидает";
        StatusColor = "#FF9800"; // Orange
    }

    public void MarkAsNotChecked()
    {
        IsChecked = false;
        StatusText = "⏳ Ожидание";
        StatusColor = "#FF9800"; // Orange
    }

    public void MarkAsSkipped()
    {
        IsChecked = false;
        StatusText = "❌ Пропущен";
        StatusColor = "#F44336"; // Red
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
