using System;
using System.IO;
using System.Windows;
using System.Windows.Threading;
using RfidScanner.Models;
using RfidScanner.Services;
using RfidScanner.ViewModels;
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

    public App()
    {
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += OnDomainUnhandledException;

        try
        {
            // Загружаем настройки
            var config = new ConfigService();
            config.Load();
            ThemeManager.SetConfigService(config);

            // Применяем сохранённую тему
            var savedTheme = config.GetTheme();
            var theme = savedTheme == "Dark" ? AppTheme.Dark : AppTheme.Light;
            ThemeManager.Apply(theme, this);

            // Пока показано окно входа, приложение не должно завершаться
            // при его закрытии (ShutdownMode по умолчанию OnLastWindowClose
            // убивает приложение, когда закрывается последнее окно —
            // им является модальное окно авторизации).
            ShutdownMode = ShutdownMode.OnExplicitShutdown;

            // Лооп авторизации: повторяем пока пользователь не войдёт или не откажется
            AppUser? authenticatedUser = null;
            RoleService? roleService = null;

            while (authenticatedUser == null)
            {
                // Пересоздаём сервисы с актуальными настройками
                var userService = new UserService();
                roleService = new RoleService();
                var loginLogService = new LoginLogService();
                var apiClient = new RfidApiClient(config.Settings.BackendUrl, config.Settings.ApiKey);

                // Показываем окно авторизации
                var loginViewModel = new LoginViewModel(userService, roleService, loginLogService, apiClient, config);
                var loginWindow = new LoginWindow(loginViewModel, config);

                // Ждём результата авторизации (модальный диалог)
                bool? loginResult = loginWindow.ShowDialog();

                if (loginResult != true)
                {
                    // Пользователь нажал "Выход" — завершаем приложение
                    Shutdown();
                    return;
                }

                authenticatedUser = loginViewModel.AuthenticatedUser;

                if (authenticatedUser == null)
                {
                    // Авторизация не удалась — пользователь может попробовать снова
                    // или закрыть окно (в этом случае loginResult будет false)
                    if (loginWindow.IsClosedByUserCancel)
                    {
                        Shutdown();
                        return;
                    }
                }
            }

            // Авторизация успешна — показываем главное окно
            var mainWindow = new MainWindow(config, roleService!, authenticatedUser);
            MainWindow = mainWindow;
            mainWindow.Show();

            // Теперь приложение должно завершаться при закрытии главного окна
            ShutdownMode = ShutdownMode.OnMainWindowClose;
        }
        catch (Exception ex)
        {
            Log(ex, "OnStartup");
            MessageBox.Show($"Ошибка запуска: {ex.Message}", "Ошибка",
                MessageBoxButton.OK, MessageBoxImage.Error);
            Shutdown();
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
