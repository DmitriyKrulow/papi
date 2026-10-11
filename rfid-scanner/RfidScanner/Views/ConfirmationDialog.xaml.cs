using System;
using System.Collections.Generic;
using System.Windows;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.Views;

/// <summary>
/// Диалог подтверждения проверки актива
/// </summary>
public partial class ConfirmationDialog : Window
{
    private readonly LocalStoreService _localStore;
    private readonly string _currentUser;

    public bool IsConfirmed => ConfirmCheckBox.IsChecked == true;

    public ConfirmationDialog(LocalStoreService localStore, string currentUser,
        string rfidTag, string assetName, string inventoryNumber, List<ScanResultItem>? history = null)
    {
        _localStore = localStore;
        _currentUser = currentUser;
        
        InitializeComponent();
        
        // Заполняем данные
        RfidTagText.Text = rfidTag;
        AssetNameText.Text = assetName;
        InventoryNumberText.Text = inventoryNumber;

        // История проверок
        if (history != null && history.Count > 0)
        {
            var sb = new System.Text.StringBuilder();
            foreach (var h in history)
            {
                sb.AppendLine($"• {h.ScannedAt:dd.MM.yyyy HH:mm} — {h.Status}");
            }
            HistoryText.Text = sb.ToString().Trim();
        }
        else
        {
            // Загружаем историю из базы
            var assetHistory = localStore.GetAssetVerificationHistory(rfidTag, 5);
            if (assetHistory.Count > 0)
            {
                var sb = new System.Text.StringBuilder();
                foreach (var h in assetHistory)
                {
                    sb.AppendLine($"• {h.ScannedAt:dd.MM.yyyy HH:mm} — {h.Status}");
                }
                HistoryText.Text = sb.ToString().Trim();
            }
        }
    }

    private void ConfirmButton_Click(object sender, RoutedEventArgs e)
    {
        if (!IsConfirmed)
        {
            MessageBox.Show("Поставьте галочку подтверждения.", "Внимание", 
                MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }
        DialogResult = true;
        Close();
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
