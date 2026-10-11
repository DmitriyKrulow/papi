using System.Collections;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Data;
using RfidScanner.Models;
using RfidScanner.Services;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for InventoryPage.xaml
/// </summary>
public partial class InventoryPage : UserControl
{
    private readonly RfidApiClient _apiClient;

    public InventoryPage()
    {
        InitializeComponent();
        
        var config = new ConfigService();
        config.Load();
        _apiClient = new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey);
        
        LoadInventories();
    }

    private async void LoadInventories()
    {
        try
        {
            var inventories = await _apiClient.GetActiveInventoriesAsync();
            InventoryList.ItemsSource = inventories;
        }
        catch
        {
            // Бэкенд не запущен — просто не показываем данные
        }
    }

    private void RefreshButton_Click(object sender, RoutedEventArgs e)
    {
        LoadInventories();
    }

    private void SearchBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter && InventoryList.ItemsSource != null)
        {
            var view = CollectionViewSource.GetDefaultView(InventoryList.ItemsSource);
            view.Filter = item =>
            {
                if (string.IsNullOrWhiteSpace(SearchBox.Text))
                    return true;
                
                var inv = item as dynamic;
                return inv.Name?.ToLower().Contains(SearchBox.Text.ToLower()) == true ||
                       inv.Department?.ToLower().Contains(SearchBox.Text.ToLower()) == true;
            };
        }
    }

    private void InventoryList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        // Здесь можно открыть детали инвентаризации
        if (InventoryList.SelectedItem is Inventory inventory)
        {
            // Открыть страницу сканирования для этой инвентаризации
        }
    }
}
