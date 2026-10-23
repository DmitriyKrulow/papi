using System.Windows.Controls;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for AuditView
/// </summary>
public partial class AuditView : UserControl
{
    private AuditViewModel? _viewModel;

    public AuditView()
    {
        InitializeComponent();
    }

    public void Initialize(AuditViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = viewModel;
    }
}
