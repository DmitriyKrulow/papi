using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

public partial class LoginWindow : Window
{
    private readonly LoginViewModel _viewModel;

    public LoginWindow(LoginViewModel viewModel)
    {
        InitializeComponent();
        _viewModel = viewModel;
        DataContext = _viewModel;

        UsernameTextBox.Focus();
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
