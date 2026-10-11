using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for ScanPage.xaml
/// </summary>
public partial class ScanPage : UserControl
{
    public ScanPage()
    {
        InitializeComponent();
    }

    private void ManualInput_TextChanged(object sender, TextChangedEventArgs e)
    {
        ManualPlaceholder.Visibility = 
            string.IsNullOrWhiteSpace(ManualInput.Text) ? Visibility.Visible : Visibility.Collapsed;
    }

    private void ManualInput_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            SendButton_Click(sender, new RoutedEventArgs());
        }
    }

    private void SendButton_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is ScanViewModel vm && !string.IsNullOrWhiteSpace(ManualInput.Text))
        {
            vm.AddChar(ManualInput.Text[0]);
            ManualInput.Text = string.Empty;
        }
    }
}
