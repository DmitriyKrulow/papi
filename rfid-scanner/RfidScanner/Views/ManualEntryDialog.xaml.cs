using System;
using System.Windows;
using System.Windows.Controls;
using RfidScanner.Models;

namespace RfidScanner.Views;

/// <summary>
/// Диалог ручного ввода актива
/// </summary>
public partial class ManualEntryDialog : Window
{
    public ManualAssetEntry? Entry { get; private set; }

    public ManualEntryDialog()
    {
        InitializeComponent();
    }

    private void AddButton_Click(object sender, RoutedEventArgs e)
    {
        // Валидация обязательных полей
        if (string.IsNullOrWhiteSpace(InventoryNumberBox.Text))
        {
            MessageBox.Show("Заполните инвентарный номер.", "Ошибка", 
                MessageBoxButton.OK, MessageBoxImage.Warning);
            InventoryNumberBox.Focus();
            return;
        }

        if (string.IsNullOrWhiteSpace(AssetNameBox.Text))
        {
            MessageBox.Show("Заполните название актива.", "Ошибка", 
                MessageBoxButton.OK, MessageBoxImage.Warning);
            AssetNameBox.Focus();
            return;
        }

        Entry = new ManualAssetEntry
        {
            InventoryNumber = InventoryNumberBox.Text.Trim(),
            AssetName = AssetNameBox.Text.Trim(),
            AssetType = AssetTypeBox.SelectedItem is ComboBoxItem ci ? ci.Content.ToString() : null,
            SerialNumber = SerialNumberBox.Text.Trim(),
            Responsible = ResponsibleBox.Text.Trim(),
            Note = NoteBox.Text.Trim()
        };

        DialogResult = true;
        Close();
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
