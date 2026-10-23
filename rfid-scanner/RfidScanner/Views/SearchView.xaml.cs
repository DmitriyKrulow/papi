using System.Windows.Controls;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for SearchView
/// </summary>
public partial class SearchView : UserControl
{
    private SearchViewModel? _viewModel;

    public SearchView()
    {
        InitializeComponent();
    }

    public void Initialize(SearchViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = viewModel;
    }
}
