using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using RfidScanner.Services;
using RfidScanner.ViewModels;
using RfidScanner.Views;

namespace RfidScanner.Views;

public partial class LoginWindow : Window
{
    private readonly LoginViewModel _viewModel;
    private readonly ConfigService _config;
    private bool _closedByUserCancel;

    public LoginWindow(LoginViewModel viewModel, ConfigService config)
    {
        InitializeComponent();
        _viewModel = viewModel;
        _config = config;
        DataContext = _viewModel;

        // Настраиваем callback для открытия настроек
        _viewModel.OnOpenSettings = () => OpenSettings();

        UsernameTextBox.Focus();
    }

    /// <summary>
    /// Показывает, что окно было закрыто кнопкой "Выход"
    /// </summary>
    public bool IsClosedByUserCancel => _closedByUserCancel;

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);
        
        // Проверяем соединение при загрузке окна
        _ = Task.Run(async () =>
        {
            await _viewModel.CheckConnectionAsync();
            
            // Обновляем UI в потоке диспетчера
            Dispatcher.Invoke(() =>
            {
                UpdateConnectionUI();
            });
        });
    }

    private void UpdateConnectionUI()
    {
        if (_viewModel.IsConnected)
        {
            ConnectionStatusBorder.Visibility = Visibility.Visible;
            NoConnectionPanel.Visibility = Visibility.Collapsed;
            ErrorTextBlock.Visibility = Visibility.Collapsed;
        }
        else
        {
            ConnectionStatusBorder.Visibility = Visibility.Collapsed;
            NoConnectionPanel.Visibility = Visibility.Visible;
            
            // Показываем ошибку только если её ещё нет
            if (string.IsNullOrEmpty(ErrorTextBlock.Text))
            {
                ErrorTextBlock.Text = "Нет соединения с сервером. Проверьте настройки подключения.";
                ErrorTextBlock.Visibility = Visibility.Visible;
            }
        }
    }

    private void OpenSettings()
    {
        var settingsWindow = new SettingsWindow(_config);
        var helper = new WindowInteropHelper(settingsWindow);
        var ownerHelper = new WindowInteropHelper(this);
        helper.Owner = ownerHelper.Handle;
        bool? result = settingsWindow.ShowDialog();

        if (result == true)
        {
            // После сохранения настроек — проверяем соединение заново
            _ = Task.Run(async () =>
            {
                await Task.Delay(200); // Даем время на сохранение
                await _viewModel.CheckConnectionAsync();
                
                Dispatcher.Invoke(() =>
                {
                    UpdateConnectionUI();
                    
                    // Очищаем сообщение об ошибке если соединение восстановлено
                    if (_viewModel.IsConnected)
                    {
                        ErrorTextBlock.Text = string.Empty;
                        ErrorTextBlock.Visibility = Visibility.Collapsed;
                    }
                });
            });
        }
    }

    private async void LoginButton_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var username = UsernameTextBox.Text;
            var password = PasswordBox.Password;

            await _viewModel.LoginAsync(username, password);

            // Если авторизация успешна — закрываем окно
            if (_viewModel.AuthenticatedUser != null)
            {
                DialogResult = true;
                Close();
            }
            else
            {
                // Показываем ошибку
                ErrorTextBlock.Text = _viewModel.ErrorMessage;
                ErrorTextBlock.Visibility = Visibility.Visible;
            }
        }
        catch (Exception ex)
        {
            ErrorTextBlock.Text = $"Ошибка входа: {ex.Message}";
            ErrorTextBlock.Visibility = Visibility.Visible;
            System.Diagnostics.Debug.WriteLine($"[LoginWindow] Error: {ex}");
        }
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        // Просто закрываем окно - приложение завершится
        _closedByUserCancel = true;
        DialogResult = false;
        Close();
    }

    private void PasswordBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            LoginButton_Click(sender, new RoutedEventArgs(Button.ClickEvent));
        }
    }
}
