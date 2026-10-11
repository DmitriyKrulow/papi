using System.Windows;
using System.Windows.Threading;
using RfidScanner.Services;
using RfidScanner.Views;

namespace RfidScanner;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        // Создаем ConfigService и MainWindow вручную (WPF не умеет с параметрами)
        var config = new ConfigService();
        config.Load();
        
        var window = new MainWindow(config);
        window.Show();
        
        // Обработка необработанных исключений
        DispatcherUnhandledException += App_DispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
    }

    private void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        MessageBox.Show($"Критическая ошибка: {e.Exception.Message}\n\n{e.Exception.StackTrace}",
            "Ошибка приложения", MessageBoxButton.OK, MessageBoxImage.Error);
        e.Handled = true;
    }

    private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        if (e.ExceptionObject is Exception ex)
        {
            MessageBox.Show($"Критическая ошибка: {ex.Message}\n\n{ex.StackTrace}",
                "Ошибка приложения", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }
}
