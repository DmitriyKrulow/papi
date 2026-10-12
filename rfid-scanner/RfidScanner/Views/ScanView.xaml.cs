using System.Windows;
using System.Windows.Controls;
using RfidScanner.ViewModels;

namespace RfidScanner.Views;

/// <summary>
/// Interaction logic for ScanView.xaml
/// </summary>
public partial class ScanView : UserControl
{
    private ScanViewModel? _viewModel;

    public ScanView()
    {
        InitializeComponent();
        // Подписываемся на загруженность для инициализации
        Loaded += ScanView_Loaded;
    }
    
    private bool _isInitialized = false;
    
    private void ScanView_Loaded(object sender, RoutedEventArgs e)
    {
        if (_isInitialized || _viewModel == null) return;
        _isInitialized = true;
        
        try
        {
            InitializeViewModel();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[ScanView_Loaded] ERROR: {ex.Message}");
        }
    }

    public void Initialize(ScanViewModel viewModel)
    {
        _viewModel = viewModel;
        DataContext = viewModel;
        // Инициализация произойдёт в Loaded
    }
    
    private void InitializeViewModel()
    {
        // Подписываемся на события изменения свойств для обновления UI
        _viewModel.PropertyChanged += (s, e) =>
        {
            if (e.PropertyName == nameof(ScanViewModel.MatchedCount))
                MatchedCountText.Text = _viewModel.MatchedCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.ExtraCount))
                ExtraCountText.Text = _viewModel.ExtraCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.MissingCount))
                MissingCountText.Text = _viewModel.MissingCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.TotalCount))
                TotalCountText.Text = _viewModel.TotalCount.ToString();
            else if (e.PropertyName == nameof(ScanViewModel.SessionRoomName))
                RoomNameText.Text = $"🏢 Помещение: {_viewModel.SessionRoomName}";
            else if (e.PropertyName == nameof(ScanViewModel.StatusText))
                StatusText.Text = _viewModel.StatusText;
            else if (e.PropertyName == nameof(ScanViewModel.LastTag))
                LastTagText.Text = string.IsNullOrEmpty(_viewModel.LastTag) ? "—" : _viewModel.LastTag;
            else if (e.PropertyName == nameof(ScanViewModel.HasResults))
                UpdateResultsList();
            else if (e.PropertyName is nameof(ScanViewModel.MatchedCount) or nameof(ScanViewModel.TotalCount))
                UpdateProgress();
        };
        
        // Обновляем имя помещения
        RoomNameText.Text = $"🏢 Помещение: {_viewModel!.SessionRoomName}";
        
        // Обновляем прогресс
        UpdateProgress();
    }
    
    private void UpdateProgress()
    {
        if (_viewModel != null)
        {
            ProgressText.Text = $"{_viewModel.MatchedCount} / {_viewModel.TotalCount}";
        }
    }
    
    private void UpdateResultsList()
    {
        if (_viewModel == null) return;
        
        ResultsList.Items.Clear();
        
        // Добавляем последние 50 результатов
        var results = _viewModel.AllResults.ToList();
        var start = Math.Max(0, results.Count - 50);
        for (int i = start; i < results.Count; i++)
        {
            ResultsList.Items.Add(results[i]);
        }
    }

    private void PauseButton_Click(object sender, RoutedEventArgs e)
    {
        if (_viewModel == null) return;
        
        _viewModel.TogglePause();
        
        if (_viewModel.IsPaused)
        {
            PauseButton.Content = "▶ Продолжить";
            StatusText.Text = "⏸ Сканирование приостановлено";
        }
        else
        {
            PauseButton.Content = "⏸ Пауза";
            StatusText.Text = "🔄 Сканирование продолжено";
        }
    }

    private void ContinueButton_Click(object sender, RoutedEventArgs e)
    {
        // Для будущего использования
        StatusText.Text = "▶ Сканирование продолжено";
    }

    private void FinishButton_Click(object sender, RoutedEventArgs e)
    {
        Finished?.Invoke();
    }

    private void ResetButton_Click(object sender, RoutedEventArgs e)
    {
        Reset?.Invoke();
    }

    private void ExitButton_Click(object sender, RoutedEventArgs e)
    {
        // Выход из режима сканирования без завершения сессии
        Exit?.Invoke();
    }

    public event Action? Finished;
    public event Action? Reset;
    public event Action? Exit;
}
