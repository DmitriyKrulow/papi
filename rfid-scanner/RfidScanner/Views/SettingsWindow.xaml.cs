using System.Windows;
using RfidScanner.Services;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for SettingsWindow.xaml
/// </summary>
public partial class SettingsWindow : Window
{
    private readonly ConfigService _config;

    public SettingsWindow(ConfigService config)
    {
        _config = config;
        InitializeComponent();
        
        // Загрузка текущих настроек
        var settings = config.Settings;
        BackendUrlBox.Text = settings.BackendUrl;
        ApiKeyBox.Text = settings.ApiKey;
        TcpIpBox.Text = settings.TcpReaderIp;
        TcpPortBox.Text = settings.TcpReaderPort.ToString();
        AutoSyncCheck.IsChecked = settings.AutoSyncOnConnect;
        SoundCheck.IsChecked = settings.EnableSound;
        
        // Установка режима сканера
        ScannerModeCombo.SelectedIndex = 
            settings.ScannerMode == ScannerMode.Tcp ? 1 : 0;
        
        // Показ/скрытие TCP-настроек
        ScannerModeCombo.SelectionChanged += (s, e) =>
        {
            TcpSettingsPanel.Visibility = 
                ScannerModeCombo.SelectedIndex == 1 ? Visibility.Visible : Visibility.Collapsed;
        };
    }

    private void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var url = BackendUrlBox.Text.TrimEnd('/');
            
            // Проверка на Punycode/Cyrillic домены — HttpClient их не поддерживает
            if (url.Contains('р') || url.Contains('ф') || url.Contains('к') || url.Contains('м'))
            {
                MessageBox.Show(
                    "URL содержит кириллический домен. HttpClient не поддерживает Punycode.\n\n" +
                    "Используйте IP-адрес (например: http://109.229.69.163:8080)",
                    "Ошибка URL",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
                return;
            }

            var settings = _config.Settings;
            settings.BackendUrl = url;
            settings.ApiKey = ApiKeyBox.Text;
            settings.TcpReaderIp = TcpIpBox.Text;
            settings.TcpReaderPort = int.TryParse(TcpPortBox.Text, out var port) ? port : 8000;
            settings.AutoSyncOnConnect = (bool)AutoSyncCheck.IsChecked!;
            settings.EnableSound = (bool)SoundCheck.IsChecked!;
            
            // Установка режима
            settings.ScannerMode = 
                ScannerModeCombo.SelectedIndex == 1 ? ScannerMode.Tcp : ScannerMode.Hid;
            
            _config.Save();
            
            DialogResult = true;
            Close();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Ошибка сохранения: {ex.Message}", "Ошибка", 
                MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
