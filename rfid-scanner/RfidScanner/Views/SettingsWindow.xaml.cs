using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
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
        // Индексы: 0=RFID, 1=NFC, 2=TCP, 3=Serial
        switch (settings.ScannerMode)
        {
            case ScannerMode.Nfc:
                ScannerModeCombo.SelectedIndex = 1;
                break;
            case ScannerMode.Tcp:
                ScannerModeCombo.SelectedIndex = 2;
                break;
            case ScannerMode.Serial:
                ScannerModeCombo.SelectedIndex = 3;
                break;
            default:
                ScannerModeCombo.SelectedIndex = 0;
                break;
        }
        
        // Обновляем индикатор режима
        UpdateModeIndicator();
        
        // Показ/скрытие TCP/Serial-настроек
        ScannerModeCombo.SelectionChanged += (s, e) =>
        {
            TcpSettingsPanel.Visibility = 
                ScannerModeCombo.SelectedIndex >= 2 ? Visibility.Visible : Visibility.Collapsed;
            UpdateModeIndicator();
        };
    }
    
    private void UpdateModeIndicator()
    {
        var selectedIndex = ScannerModeCombo.SelectedIndex;
        
        switch (selectedIndex)
        {
            case 1: // NFC
                ModeIndicatorIcon.Text = "📱";
                ModeIndicatorText.Text = "NFC-сканер (клавиатура)";
                ModeIndicatorBorder.Background = (Brush)FindResource("ThemeWidgetSuccessBg");
                ModeIndicatorText.Foreground = (Brush)FindResource("ThemeSuccess");
                break;
            case 2: // TCP
                ModeIndicatorIcon.Text = "🌐";
                ModeIndicatorText.Text = "TCP/IP сканер";
                ModeIndicatorBorder.Background = (Brush)FindResource("ThemeWidgetInfoBg");
                ModeIndicatorText.Foreground = (Brush)FindResource("ThemeInfo");
                break;
            case 3: // Serial
                ModeIndicatorIcon.Text = "🔌";
                ModeIndicatorText.Text = "Serial (RS232) сканер";
                ModeIndicatorBorder.Background = (Brush)FindResource("ThemeWidgetWarningBg");
                ModeIndicatorText.Foreground = (Brush)FindResource("ThemeWarning");
                break;
            default: // RFID
                ModeIndicatorIcon.Text = "📡";
                ModeIndicatorText.Text = "RFID-сканер (HID)";
                ModeIndicatorBorder.Background = (Brush)FindResource("ThemeWidgetErrorBg");
                ModeIndicatorText.Foreground = (Brush)FindResource("ThemeError");
                break;
        }
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
            // Индексы: 0=RFID, 1=NFC, 2=TCP, 3=Serial
            settings.ScannerMode = ScannerModeCombo.SelectedIndex switch
            {
                1 => ScannerMode.Nfc,
                2 => ScannerMode.Tcp,
                3 => ScannerMode.Serial,
                _ => ScannerMode.Hid
            };
            
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
