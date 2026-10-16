using System;
using System.IO;
using System.Windows;
using System.Windows.Threading;
using RfidScanner.Services;
using RfidScanner.Views;

namespace RfidScanner;

public partial class App : Application
{
    private static readonly string LogPath =
        @"C:\Users\Public\PAPI\RfidScanner\logs\error.log";

    // Защита от рекурсии: MessageBox.Show запускает вложенный цикл сообщений,
    // и повторяющееся исключение вызывало бы MessageBox.Show бесконечно
    // (каскад приводил к StackOverflowException).
    private static bool _errorDialogShown;

    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += OnDomainUnhandledException;

        try
        {
            var config = new ConfigService();
            config.Load();

            var window = new MainWindow(config);
            window.Show();
        }
        catch (Exception ex)
        {
            Log(ex, "OnStartup");
            MessageBox.Show($"Ошибка запуска: {ex.Message}", "Ошибка",
                MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs args)
    {
        Log(args.Exception, "Dispatcher");
        ShowErrorOnce(args.Exception);
        args.Handled = true;
    }

    private void OnDomainUnhandledException(object sender, UnhandledExceptionEventArgs args)
    {
        if (args.ExceptionObject is Exception ex)
        {
            Log(ex, "AppDomain");
            ShowErrorOnce(ex);
        }
    }

    private static void ShowErrorOnce(Exception ex)
    {
        if (_errorDialogShown) return;
        _errorDialogShown = true;

        try
        {
            MessageBox.Show($"Ошибка: {ex.Message}\n\nПодробности: {LogPath}",
                "Ошибка", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        catch
        {
            // Диалог не критичен — главное не уйти в рекурсию
        }
        finally
        {
            // Разрешаем показать следующее сообщение после завершения текущего
            Current?.Dispatcher.BeginInvoke(new Action(() => _errorDialogShown = false));
        }
    }

    private static void Log(Exception ex, string source)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(LogPath)!);
            File.AppendAllText(LogPath,
                $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {source}: {ex}\n\n");
        }
        catch
        {
            // Логирование не должно ронять приложение
        }
    }
}
