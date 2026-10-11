using System.Windows;
using System.Windows.Input;
using RfidScanner.Services;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    private readonly ConfigService _config;
    private readonly ScanViewModel _scanViewModel;

    public MainWindow(ConfigService config)
    {
        _config = config;
        config.Load();
        
        InitializeComponent();
        
        // Инициализация ViewModel
        _scanViewModel = new ScanViewModel(
            new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey),
            new OfflineQueueService(),
            config);
        
        ScanPageControl.DataContext = _scanViewModel;
        InventoryPageControl.DataContext = new InventoryViewModel(
            new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey),
            new OfflineQueueService());
        
        // Настройка обработки клавиш для HID-сканера
        PreviewKeyDown += MainWindow_PreviewKeyDown;
        
        // Статус подключения — без ошибок при отсутствии бэкенда
        StatusText.Text = "Нет подключения";
        StatusText.Foreground = System.Windows.Media.Brushes.Orange;
    }

    private void MainWindow_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        // HID-сканер вводит RFID-тег + Enter
        // Пропускаем системные клавиши
        if (e.Key >= Key.D0 && e.Key <= Key.Z)
        {
            var charCode = char.ToLower((char)e.Key);
            _scanViewModel.AddChar(charCode);
            e.Handled = true;
        }
        else if (e.Key >= Key.NumPad0 && e.Key <= Key.NumPad9)
        {
            var charCode = (char)(e.Key - Key.NumPad0 + '0');
            _scanViewModel.AddChar(charCode);
            e.Handled = true;
        }
        else if (e.Key == Key.Return || e.Key == Key.Enter)
        {
            _scanViewModel.ProcessCurrentTag();
            e.Handled = true;
        }
    }

    private async void CheckConnectionAsync()
    {
        try
        {
            var apiClient = new RfidApiClient(_config.Settings.BackendUrl, _config.Settings.ApiKey);
            var connected = await apiClient.AuthenticateAsync();
            
            Application.Current.Dispatcher.Invoke(() =>
            {
                StatusText.Text = connected ? "Подключено" : "Нет подключения к API";
                StatusText.Foreground = connected ? 
                    System.Windows.Media.Brushes.LightGreen : 
                    System.Windows.Media.Brushes.Orange;
            });
            
            apiClient.Dispose();
        }
        catch
        {
            // Не показываем ошибку — просто статус "Нет подключения"
            Application.Current.Dispatcher.Invoke(() =>
            {
                StatusText.Text = "Нет подключения к API";
                StatusText.Foreground = System.Windows.Media.Brushes.Orange;
            });
        }
    }

    private void SettingsButton_Click(object sender, RoutedEventArgs e)
    {
        var settingsWindow = new SettingsWindow(_config);
        settingsWindow.ShowDialog();
        
        // Перезагрузка с новыми настройками
        RefreshWithNewSettings();
    }

    private void RefreshWithNewSettings()
    {
        _config.Load();
        CheckConnectionAsync();
    }
}
