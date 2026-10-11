using System.Windows;
using RfidScanner.Services;
using RfidScanner.Views;

namespace RfidScanner;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        var config = new ConfigService();
        config.Load();
        
        var window = new MainWindow(config);
        window.Show();
        
        DispatcherUnhandledException += (s, args) =>
        {
            MessageBox.Show($"Ошибка: {args.Exception.Message}", "Ошибка", 
                MessageBoxButton.OK, MessageBoxImage.Error);
            args.Handled = true;
        };
    }
}
