using System;
using System.Windows;
using RfidScanner.Models;

namespace RfidScanner.Views;

/// <summary>
/// Диалог деталей актива
/// </summary>
public partial class AssetDetailDialog : Window
{
    private ScanResultItem? _currentItem;

    public AssetDetailDialog()
    {
        InitializeComponent();
    }

    public void SetData(string rfidTag, string assetName, string inventoryNumber,
        ScanAssetStatus status, string? note, DateTime scannedAt)
    {
        _currentItem = new ScanResultItem
        {
            RfidTag = rfidTag,
            AssetName = assetName,
            InventoryNumber = inventoryNumber,
            Status = status,
            Note = note,
            ScannedAt = scannedAt
        };

        // Заполняем данные
        RfidTagText.Text = $"RFID: {rfidTag}";
        AssetNameText.Text = assetName;
        InventoryNumberText.Text = inventoryNumber;
        ScannedAtText.Text = scannedAt.ToString("dd.MM.yyyy HH:mm:ss");
        NoteTextBox.Text = note ?? "";

        // Статус с иконкой и цветом
        var statusInfo = GetStatusInfo(status);
        StatusText.Text = $"{statusInfo.Icon} {statusInfo.Text}";
        StatusText.Foreground = statusInfo.Brush;
    }

    private (string Icon, string Text, System.Windows.Media.Brush Brush) GetStatusInfo(ScanAssetStatus status)
    {
        return status switch
        {
            ScanAssetStatus.Matched => ("✅", "Совпадает", System.Windows.Media.Brushes.Green),
            ScanAssetStatus.Extra => ("⚠️", "Лишний актив", System.Windows.Media.Brushes.Orange),
            ScanAssetStatus.Missing => ("❌", "Не найден", System.Windows.Media.Brushes.Red),
            _ => ("❓", "Ошибка", System.Windows.Media.Brushes.Gray)
        };
    }

    private void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        if (_currentItem != null)
        {
            _currentItem.Note = NoteTextBox.Text;
            // Здесь можно добавить отправку на сервер
        }
        DialogResult = true;
        Close();
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
